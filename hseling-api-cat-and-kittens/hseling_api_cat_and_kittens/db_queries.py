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

    string2syntrole_id = get_syntroles_dict()
    string2morph_id = get_morph_dict()

    if morph1 == None:
        morph1 = ""
    if morph2 == None:
        morph2 = ""
    
    if isinstance(morph1, str):
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
        pos1 = ""
        morph1 = ""

    if isinstance(morph2, str):
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
        pos2 = ""
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
        if min_ != "" and min_ > -1 and min_ < 5:
            min_ = int(min_)
        elif min_ != "" and min_ > 4:
            min_ = 4
        else:
            min_ = 0
    else:
        min_ = 0

    if isinstance(max_, str):
        if max_ != "" and max_ > 0 and max_ < 6:
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
            sys.exit("A fatal error occured!")
        
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
        WHERE unigrams.unigram = %s AND original_cat = 1) as tab2
        ON tab2.collocate_id = tab1.id_unigram
        ORDER BY ''' + search_metric + ''' DESC
        LIMIT 20;'''
        cur.execute(stmt, (search_token, ))
        row_headers = [x[0] for x in cur.description]
        rv = cur.fetchall()
        json_data = []
        for result in rv:
            json_data.append(dict(zip(row_headers, result)))
        
        return json_data

    else:
        return ['']

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
    stmt= """SELECT tab2.id_unigram, tab2.pos, tab2.morph, words.id_word, words.id_sent, tab2.freq_all FROM (
            SELECT tab1.id_unigram, tab1.unigram, tab1.pos, pos.id_pos, morph, freq_all, original_cat FROM (    
                                SELECT uni.id_unigram, uni.unigram, pos, morph, freq_all, original_cat
                                FROM unigrams uni
                                INNER JOIN unitags tags ON uni.id_unigram = tags.id_unigram
                                WHERE BINARY uni.unigram = %s
                                ORDER BY freq_all DESC
                                LIMIT 2
                            ) AS tab1
                            INNER JOIN pos pos ON tab1.pos = pos.pos
                            WHERE pos.id_pos REGEXP """ + pos1 + """ 
                            AND morph LIKE '%""" + morph1 + """%'
                            AND morph <> '_'
                            ORDER BY freq_all DESC) AS tab2
                            INNER JOIN words ON tab2.id_unigram = words.id_unigram LIMIT 10;"""
    cur.execute(stmt, (lemma1, ))
    result = cur.fetchall()
    word1_id_list = [{"id_word" : word[3], "id_sent" : word[4]} for word in result] 
    sent_list = []

    for word1 in word1_id_list:
        id_sent = str(word1["id_sent"])
        word1_id = word1["id_word"]
        stmt = """SELECT word_tab.id_word, uni.freq_all FROM
                    (SELECT id_word, id_unigram FROM words WHERE id_word >= """ + str(word1_id + min_) + """
                    AND id_word <= """ + str(word1_id + max_) + """
                    AND id_sent = """ + id_sent + """) AS word_tab
                        INNER JOIN unigrams uni ON word_tab.id_unigram = uni.id_unigram
                        INNER JOIN unitags tags ON uni.id_unigram = tags.id_unigram
                        INNER JOIN pos pos ON tags.pos = pos.pos
                    WHERE pos.id_pos REGEXP """ + pos2 + """
                    AND morph LIKE '%""" + morph1 + """%'
                    AND morph <> '_' 
                    ORDER BY uni.freq_all DESC LIMIT 10;"""
        cur.execute(stmt)
        result = cur.fetchall()
        word1_word2_result = []

        if syntrole != "_":
            for line in result:
                stmt = """SELECT * FROM wordpairs
                        WHERE synt_role_id = """ + syntrole + """
                        AND head_id = """ + word1 + """
                        AND dependent_id = """ + line[0] + """
                        ;"""
                cur.execute(stmt)
                res = cur.fetchall()
                if res:
                    result_dict = {"id_sent" : word1["id_sent"], "word1" : word1["id_word"], "word2" : line[0]}
                    word1_word2_result.append(result_dict)
                else:
                    continue
        else:
            for line in result:
                result_dict = {"id_sent" : word1["id_sent"], "word1" : word1["id_word"], "word2" : line[0]}
                word1_word2_result.append(result_dict)
        
        for result_dict in word1_word2_result:
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
            sent_list.append(sent)

    row_headers = ["Example sentence"]
    json_data = []
    for sent in sent_list:
        json_data.append(dict(zip(row_headers, [sent])))
    
    return json_data
