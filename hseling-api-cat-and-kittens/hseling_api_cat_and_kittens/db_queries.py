from hseling_api_cat_and_kittens import boilerplate
import sys
import re, string

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

def bigram_search(search_token, search_metric, search_domain):

    """
    produces list of most common bigram according to the first collocate (input by user);
    search_token : user input word
    search_metric : user selected metric for result sorting
    search_domain : user selected domain of search
    """

    if search_metric in ['frequency', 'pmi', 'logdice', 't_score']:
        print("search metric found!!")
        if search_domain and search_domain != '_':
            frequency = f'd{search_domain}_freq'
            pmi = f'd{search_domain}_pmi'
            tscore = f'd{search_domain}_tsc'
            logdice = f'd{search_domain}_logdice'

        elif search_domain and search_domain == '_': 
            frequency = 'raw_frequency'
            pmi = 'pmi'
            tscore = 'tscore'
            logdice = 'logdice'
        
        else:
            print("A fatal error occured!")
        


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

def check_syntrole(result, word, syntrole):

    cur = CONN.cursor()
    word1_word2_result = []

    if syntrole != "_":
        print("actually checking syntrole")
        for line in result:
            stmt = """SELECT * FROM wordpairs
                    WHERE synt_role_id = """ + syntrole + """
                    AND head_id = """ + word + """
                    AND dependent_id = """ + line[0] + """
                    ;"""
            cur.execute(stmt)
            res = cur.fetchall()
            if res:
                result_dict = {"id_sent" : word["id_sent"], "word1" : word["id_word"], "word2" : line[0]}
                word1_word2_result.append(result_dict)
            else:
                continue
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

    stmt = """SELECT tab1.id_unigram FROM (    
                                SELECT uni.id_unigram, uni.unigram, pos, morph, freq_all, original_cat
                                FROM unigrams uni
                                INNER JOIN unitags tags ON uni.id_unigram = tags.id_unigram
                                WHERE uni.unigram REGEXP {}
                                AND morph LIKE '%{}%'
                                ORDER BY freq_all DESC
                                LIMIT 3
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

def single_token_search(search_token):
    """
    search sentences containing input lemma
    search token : input token
    """

    cur = CONN.cursor()

    cur.execute("SELECT unigram, id_unigram, freq_all FROM unigrams WHERE BINARY unigram = %s ORDER BY freq_all DESC LIMIT 3;", (search_token, ))

    list_id_unigram = cur.fetchall()
    dict_unigram_sent = {elem[1] : [] for elem in list_id_unigram}

    stmt = "SELECT id_sent FROM words WHERE"
    for id_unigram in dict_unigram_sent.keys():
        stmt = "SELECT id_sent, id_word FROM words WHERE id_unigram = " + str(id_unigram) + " LIMIT 2;"
        cur.execute(stmt)
        list_id_sent = cur.fetchall()
        for id_ in list_id_sent:
            dict_unigram_sent[id_unigram].append({"id_sent": id_[0], "id_word": id_[1]})

    sent_list = []

    for value in dict_unigram_sent.values():
        for example in value:
            id_sent = str(example["id_sent"])
            search_token_id = example["id_word"]
            sent_start = str(example["id_word"] - 5)
            sent_end = str(example["id_word"] + 5)
            stmt = f"SELECT id_word, word FROM words WHERE id_sent = {id_sent} AND "
            stmt += f"(id_word >= {sent_start} AND id_word < {sent_end})"
            stmt += f""
            cur.execute(stmt)
            sent = cur.fetchall()
            sent = ["%%%" + word[1] + "%%%" if word[0] == search_token_id else word[1] for word in sent]
            sent = ''.join([('' if c in string.punctuation and c != "(" else ' ')+c for c in sent]).strip()
            sent = re.sub('^[{}]\s+'.format(string.punctuation), '', sent)
            sent = re.sub('(?<=\()\s', '', sent)
            sent_list.append(sent)

    row_headers = ["Example sentence"]
    json_data = []
    for sent in sent_list:
        json_data.append(dict(zip(row_headers, [sent])))
    
    return json_data

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

    row_headers = ["Example sentence"]
    json_data = []
    for sent in sent_list:
        json_data.append(dict(zip(row_headers, [sent])))
    return json_data
