from hseling_api_cat_and_kittens import boilerplate
import sys
import re, string
import random

CONN = boilerplate.get_mysql_connection()

def get_syntroles_dict():
    cur = CONN.cursor()
    cur.execute("SELECT * FROM syntroles;")
    syntrole_list = cur.fetchall()
    string2syntrole_id = {row[1] : row[0] for row in syntrole_list} 
    return string2syntrole_id

def get_morph_dict():
    cur = CONN.cursor()
    cur.execute("SELECT * FROM pos;")
    morph_list = cur.fetchall()
    string2morph_id = {row[1] : row[0] for row in morph_list}
    return string2morph_id

def get_domain_dictionary():
    cur = CONN.cursor()
    cur.execute("SELECT * FROM domains;")
    domain_list = cur.fetchall()
    domain_name2id = {row[1] : str(row[0]) for row in domain_list}
    return domain_name2id

def get_values(lemma1, lemma2, morph1, morph2, syntrole, min_, max_):

    if isinstance(lemma1, str):
        if lemma1 == "":
            lemma1 = "'^(.*?)$'"
        else:
            lemma1 = "'^" + lemma1  + "$'"

    if isinstance(lemma2, str):
        if lemma2 == "":
            lemma2 = "'^(.*?)$'"
        else:
            lemma2 = "'^" + lemma2 + "$'"

    string2syntrole_id = get_syntroles_dict()
    string2morph_id = get_morph_dict()

    if morph1 == None:
        morph1 = ""
    if morph2 == None:
        morph2 = ""
    
    if isinstance(morph1, str) and morph1 != "":
        morph1_list = morph1.split(',')
        if morph1_list[0] in string2morph_id.keys():
            pos1 = "'^" + str(string2morph_id[morph1_list[0]]) + "$'"
            try:
                morph1_list = morph1_list[1:]
                morph1 = '|'.join(morph1_list)
            except IndexError:
                morph1 = ""
        else:
            pos1 = "'^[0-9]+$'"
    else:
        pos1 = "'^[0-9]+$'"
        morph1 = ""

    if isinstance(morph2, str) and morph2 != "":
        morph2_list = morph2.split(',')
        if morph2_list[0] in string2morph_id.keys():
            pos2 = "'^" + str(string2morph_id[morph2_list[0]]) + "$'"
            try:
                morph2_list = morph2_list[1:]
                morph2 = '|'.join(morph2_list)
            except IndexError:
                morph2 = ""
        else:
            pos2 = "'^[0-9]+$'"
    else:
        pos2 = "'^[0-9]+$'"
        morph2 = ""
        
    if isinstance(syntrole, str):
        syntrole = syntrole.split('-')[0]
        if syntrole in string2syntrole_id.keys():
            syntrole = str(string2syntrole_id[syntrole])
        else:
            syntrole = "_"
    else:
        syntrole = "_"

    if isinstance(min_, str):
        if min_ == "":
            min_ = 0
        else:
            min_ = int(min_)
            if min_ > -1 and min_ < 5:
                min_ = int(min_)
            elif min_ > 4:
                min_ = 4
            else:
                min_ = 0        
    else:
        min_ = 0

    if isinstance(max_, str):
        if max_ == "":
            max_ = 1
        else:
            max_ = int(max_)
            if max_ > 0 and max_ < 6:
                max_ = int(max_)
            elif max_ != "" and max_ > 5:
                max_ = 5
            else:
                max_ = 1        
    else:
        max_ = 1 

    return lemma1, lemma2, pos1, pos2, morph1, morph2, syntrole, min_, max_

def freq_search(search_token):
    '''
    get the best fitting bigram
    search_token : word input from user
    '''
    frequency = 'freq_all'
    cur = CONN.cursor()
    stmt = """SELECT unigrams.""" + frequency + """ AS frequency, lemmas.lemma AS lemma
    FROM (SELECT * FROM unigrams WHERE original_cat = 1) AS unigrams
    JOIN lemmas ON unigrams.lemma = lemmas.id_lemmas
    WHERE unigrams.unigram = %(src_token)s
    ORDER BY frequency DESC;"""
    cur.execute(stmt, {'src_token' : search_token})
    row_headers = [x[0] for x in cur.description]
    rv = cur.fetchall()
    json_data = []
    for result in rv:
        json_data.append(dict(zip(row_headers, result)))
    
    return json_data

def check_syntrole(result, word, syntrole):

    cur = CONN.cursor()
    word1_word2_result = []

    if syntrole != "_":
        print("actually checking syntrole")
        for line in result:
            print(type(line[0]))
            stmt = '''SELECT * FROM wordpairs
                    WHERE synt_role_id = "''' + str(syntrole) + '''"
                    AND head_id = ''' + str(word["id_word"]) + '''
                    AND dependent_id = "''' + str(line[0]) + '''"
                    ;'''
            cur.execute(stmt)
            res = cur.fetchall()
            if res:
                result_dict = {"id_sent" : word["id_sent"], "word1" : word["id_word"], "word2" : line[0]}
                word1_word2_result.append(result_dict)
            else:
                result_dict = {"id_sent" : 0, "word1" : 0, "word2" : 0}
                word1_word2_result.append(result_dict)
    else:
        for line in result:
            result_dict = {"id_sent" : word["id_sent"], "word1" : word["id_word"], "word2" : line[0]}
            word1_word2_result.append(result_dict)

    return word1_word2_result

def generate_sent(result):

    cur = CONN.cursor()
    for result_dict in result:
        id_sent = str(result_dict["id_sent"])
        word1 = result_dict["word1"]
        word2 = result_dict["word2"]
        sent_start = str(result_dict["word1"] - 10)
        sent_end = str(result_dict["word2"] + 10)
        stmt = f"SELECT id_word, word FROM words WHERE id_sent = {id_sent} AND "
        stmt += f"(id_word >= {sent_start} AND id_word < {sent_end})"
        stmt += f""
        cur.execute(stmt)
        sent = cur.fetchall()
        sent = ["%%%" + word[1] + "%%%" if word[0] == word1 or word[0] == word2 else word[1] for word in sent]
        sent = ''.join([('' if c in string.punctuation and c != "(" else ' ')+c for c in sent]).strip()
        sent = re.sub('^[{}]\s+'.format(string.punctuation), '', sent)
        sent = re.sub('(?<=\()\s', '', sent)
        return sent

def get_words4lemma(lemma, morph, pos):
    cur = CONN.cursor()
    word_id_list = list()

    """SELECT temp.id_unigram, temp.unigram, pos, morph, freq_all FROM  
    (SELECT t.*,  @row_num :=@row_num + 1 AS row_num FROM unigrams t,      
    (SELECT @row_num:=0) counter ORDER BY freq_all) temp
    INNER JOIN unitags tags ON temp.id_unigram = tags.id_unigram
    WHERE temp.row_num >= ROUND (.95* @row_num) 
    AND temp.unigram REGEXP {}
    AND temp.morph LIKE '%{}%' 
    AND temp.original_cat = 1
    ORDER BY freq_all DESC;"""

    stmt = """SELECT tab1.id_unigram FROM (    
                                SELECT temp.id_unigram, temp.unigram, pos, morph, freq_all FROM  
                                (SELECT t.*,  @row_num :=@row_num + 1 AS row_num FROM unigrams t,      
                                (SELECT @row_num:=0) counter ORDER BY freq_all) temp
                                INNER JOIN unitags tags ON temp.id_unigram = tags.id_unigram
                                WHERE temp.row_num >= ROUND (.95* @row_num) 
                                AND temp.unigram REGEXP {}
                                AND temp.morph LIKE '%{}%' 
                                AND temp.original_cat = 1
                                ORDER BY freq_all DESC
                            ) AS tab1
                            INNER JOIN pos pos ON tab1.pos = pos.pos
                            WHERE pos.id_pos REGEXP {};"""
    stmt_word = stmt.format(lemma, morph, pos)
    cur.execute(stmt_word)
    result = cur.fetchall()
    for id_unigram in result:
        sub_stmt = """SELECT words.id_word, words.id_sent
                FROM unigrams
                JOIN words
                ON unigrams.id_unigram = words.id_unigram
                WHERE unigrams.id_unigram = """ + str(id_unigram[0]) + """
                LIMIT 3;"""
        cur.execute(sub_stmt)
        result = cur.fetchall()
        word_id_list.extend([{"id_word" : word[0], "id_sent" : word[1]} for word in result])
    return word_id_list

def lemma_search(lemma1, lemma2, morph1, morph2, syntrole, min_, max_):
    
    lemma1, lemma2, pos1, pos2, morph1, morph2, syntrole, min_, max_ = get_values(lemma1, lemma2, morph1, morph2, syntrole, min_, max_)

    cur = CONN.cursor()

    word1_id_list = get_words4lemma(lemma1, morph1, pos1)
    word2_id_list = get_words4lemma(lemma2, morph2, pos2)
    sent_list = list()
    print(word1_id_list)
    print(word2_id_list)

    if word1_id_list and word2_id_list and lemma1 != "'^(.*?)$'" and lemma2 != "'^(.*?)$'":
        for word1 in word1_id_list:
            id_sent = str(word1["id_sent"])
            word1_id = word1["id_word"]
            i = 0
            for word2 in word2_id_list:
                if i < 25:
                    id_sent2 = str(word2["id_sent"])
                    word2_id = word2["id_word"]
                    if id_sent == id_sent2 and word2_id >= word1_id + min_ and word2_id <= word1_id + max_:
                        i += 1
                        stmt = """SELECT word_tab.id_word, uni.freq_all FROM
                            (SELECT id_word, id_unigram FROM words WHERE id_word >= {}
                            AND id_word <= {}
                            AND id_sent = {}) AS word_tab
                                INNER JOIN unigrams uni ON word_tab.id_unigram = uni.id_unigram
                                INNER JOIN unitags tags ON uni.id_unigram = tags.id_unigram
                                INNER JOIN pos pos ON tags.pos = pos.pos
                            WHERE pos.id_pos REGEXP {}
                            AND morph LIKE '%{}%'
                            AND morph <> '_' 
                            ORDER BY uni.freq_all DESC LIMIT 50;"""
                        stmt_word1 = stmt.format(str(word1_id + min_), str(word1_id + max_), str(word2_id), id_sent, pos2, morph2)
                        cur.execute(stmt_word1)
                        result = cur.fetchall()
                        word1_word2_result = check_syntrole(result, word1, syntrole)
                        sent = generate_sent(word1_word2_result)
                        if sent:
                            sent_list.append(sent)
                else:
                    break
    
    elif word1_id_list and lemma2 == "'^(.*?)$'":
        for word1 in word1_id_list:
            id_sent = str(word1["id_sent"])
            word1_id = word1["id_word"]
            stmt = """SELECT word_tab.id_word, uni.freq_all FROM
                            (SELECT id_word, id_unigram FROM words WHERE id_word >= {}
                            AND id_word <= {}
                            AND id_sent = {}) AS word_tab
                                INNER JOIN unigrams uni ON word_tab.id_unigram = uni.id_unigram
                                INNER JOIN unitags tags ON uni.id_unigram = tags.id_unigram
                                INNER JOIN pos pos ON tags.pos = pos.pos
                            WHERE morph <> '_' 
                            ORDER BY uni.freq_all DESC LIMIT 50;"""
            stmt_word1 = stmt.format(str(word1_id + min_), str(word1_id + max_), id_sent)
            cur.execute(stmt_word1)
            result = cur.fetchall()
            word1_word2_result = check_syntrole(result, word1, syntrole)
            sent = generate_sent(word1_word2_result)
            if sent:
                sent_list.append(sent)
    
    elif word2_id_list and lemma1 == "'^(.*?)$'":
        for word2 in word2_id_list:
            id_sent = str(word2["id_sent"])
            word2_id = word2["id_word"]
            stmt = """SELECT word_tab.id_word, uni.freq_all FROM
                            (SELECT id_word, id_unigram FROM words WHERE id_word >= {}
                            AND id_word <= {}
                            AND id_sent = {}) AS word_tab
                                INNER JOIN unigrams uni ON word_tab.id_unigram = uni.id_unigram
                                INNER JOIN unitags tags ON uni.id_unigram = tags.id_unigram
                                INNER JOIN pos pos ON tags.pos = pos.pos
                            WHERE morph <> '_' 
                            ORDER BY uni.freq_all DESC LIMIT 50;"""
            stmt_word2 = stmt.format(str(word2_id - max_), str(word2_id + min_), id_sent)
            cur.execute(stmt_word2)
            result = cur.fetchall()
            word1_word2_result = check_syntrole(result, word2, syntrole)
            sent = generate_sent(word1_word2_result)
            if sent:
                sent_list.append(sent)
    else:
        return sent_list

    row_headers = ["Примерные предложения"]
    json_data = []
    for sent in sent_list:
        json_data.append(dict(zip(row_headers, [sent])))
    return json_data


def single_token_search(search_token, search_domain):
    """
    search sentences containing input lemma
    search token : input token
    """
    domain_name2id = get_domain_dictionary()
    domain = domain_name2id.get(search_domain)

    if domain:
        frequency = f'freq{domain}'
    else:   
        frequency = 'freq_all'

    cur = CONN.cursor()
    stmt = """SELECT unigram, id_unigram, """ + frequency + """ FROM  
    (SELECT t.*,  @row_num :=@row_num + 1 AS row_num FROM unigrams t,      
    (SELECT @row_num:=0) counter ORDER BY """ + frequency + """) temp 
    WHERE temp.row_num >= ROUND (.95* @row_num) 
    AND temp.unigram = %s
    AND temp.original_cat = 1
    ORDER BY freq_all DESC;"""

    cur.execute(stmt, (search_token, ))

    list_id_unigram = cur.fetchall()
    dict_unigram_sent = {elem[1] : [] for elem in list_id_unigram}

    stmt = """SELECT COUNT(*) FROM words WHERE id_unigram in (""" + ', '.join(str(key) for key in dict_unigram_sent.keys()) + """);"""
    cur.execute(stmt)
    count_list = cur.fetchall()
    count = count_list[0][0]

    full_list_sentences = list()
    for id_unigram in dict_unigram_sent.keys():

        stmt = """SELECT w.id_sent, w.id_word, w.id_text, meta.author, meta.year, meta.title FROM 
                  (SELECT id_sent, id_word, id_text
                  FROM words  
                  WHERE id_unigram = """ + str(id_unigram) + """) AS w 
                    JOIN metadata meta ON w.id_text = meta.id_text
                  ORDER BY RAND()
                  LIMIT 5;"""
        cur.execute(stmt)
        list_id_sent = cur.fetchall()
        full_list_sentences.extend(list_id_sent)

    sent_list = list()

    for example in full_list_sentences:
        id_sent = str(example[0])
        id_token = example[1]
        id_text = str(example[2])
        author = str(example[3])
        year = str(example[4])
        title = str(example[5])

        ## MAIN PARAGRAPH
        stmt = f"SELECT id_word, word FROM words WHERE id_sent = {id_sent} AND id_text = {id_text};"
        cur.execute(stmt)
        main_paragraph = cur.fetchall()
        main_paragraph = stringify_sent(main_paragraph, id_token)

        ## 1st PARAGRAPH
        stmt = f"SELECT id_word, word FROM words WHERE id_sent = {str(int(id_sent) - 1)} AND id_text = {id_text};"
        cur.execute(stmt)
        first_paragraph = cur.fetchall()
        # first_paragraph = "<p class='hidden-paragraph'>" + stringify_sent(first_paragraph, id_token) + "</p>"
        first_paragraph = stringify_sent(first_paragraph, id_token)

        ## LAST PARAGRAPH
        stmt = f"SELECT id_word, word FROM words WHERE id_sent = {str(int(id_sent) + 1)} AND id_text = {id_text};"
        cur.execute(stmt)
        last_paragraph = cur.fetchall()
        # last_paragraph = "<p class='hidden-paragraph'>" + stringify_sent(last_paragraph, id_token) + "</p>"
        last_paragraph = stringify_sent(last_paragraph, id_token)

        ## REFERENCE
        # reference = f" <p class='italics'>({author}, {year}, {title})</p>"
        reference = f"{author}, {year}, {title}"
        
        # sent = first_paragraph + main_paragraph + last_paragraph + reference
        sent = (first_paragraph, main_paragraph, last_paragraph, reference)
        sent_list.append(sent)

    row_headers = [f"Примерные предложения, количестко найденных текстов: {count} (мы показываем только их часть)"]
    json_data = []
    for sent in sent_list:
        json_data.append(dict(zip(row_headers, [sent])))
    
    return json_data

def stringify_sent(sent_db_result, word_to_boldify):
    sent = ["<strong>" + word[1] + "</strong>" if word[0] == word_to_boldify else word[1] for word in sent_db_result]
    sent = ''.join([('' if c in string.punctuation and c != "(" else ' ')+c for c in sent]).strip()
    sent = re.sub('^[{}]\s+'.format(string.punctuation), '', sent)
    sent = re.sub('(?<=\()\s', '', sent)
    return sent

def collocation_search(search_token, search_metric, search_domain):

    """
    produces list of most common bigram according to the first collocate (input by user);
    search_token : user input word
    search_metric : user selected metric for result sorting
    search_domain : user selected domain of search
    """

    domain_name2id = get_domain_dictionary()

    if search_metric in ['frequency', 'pmi', 'logdice', 't_score']:

        domain = domain_name2id.get(search_domain)

        if domain:
            frequency = f'd{domain}_freq'
            pmi = f'd{domain}_pmi'
            tscore = f'd{domain}_tsc'
            logdice = f'd{domain}_logdice'

        else:   
            frequency = 'raw_frequency'
            pmi = 'pmi'
            tscore = 'tscore'
            logdice = 'logdice'
        
        cur = CONN.cursor()
        stmt = '''SELECT tab2.unigram_token as entered_search, 
        tab1.unigram as collocate,
        frequency,
        pmi,
        t_score,
        logdice
        FROM unigrams as tab1
        JOIN
        (SELECT 
        unigrams.unigram as unigram_token, 
        2grams.wordform_2 as collocate_id, 
        2grams.''' + frequency + ''' as frequency,
        2grams.''' + pmi + ''' as pmi,
        2grams.''' + tscore + ''' as t_score,
        2grams.''' + logdice + ''' as logdice
        FROM unigrams
        JOIN 2grams ON unigrams.id_unigram = 2grams.wordform_1 
        WHERE unigrams.unigram = %s AND unigrams.original_cat = 1) as tab2
        ON tab2.collocate_id = tab1.id_unigram
        ORDER BY ''' + search_metric + ''' DESC
        LIMIT 20;'''
        cur.execute(stmt, (search_token, ))
        row_headers = [x[0] for x in cur.description]
        rv = cur.fetchall()
        json_data = []
        for result in rv:
            json_data.append(dict(zip(row_headers, result)))
        print(json_data)
        return json_data
        

    else:
        return ['']