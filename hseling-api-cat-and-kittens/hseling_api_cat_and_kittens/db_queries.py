from hseling_api_cat_and_kittens import boilerplate
import sys
import re, string
import random

CONN = boilerplate.get_mysql_connection()

# def get_syntroles_dict():
#     cur = CONN.cursor()
#     cur.execute("SELECT * FROM syntroles;")
#     syntrole_list = cur.fetchall()
#     string2syntrole_id = {row[1] : row[0] for row in syntrole_list} 
#     return string2syntrole_id

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

def get_id2domain_dictionary():
    cur = CONN.cursor()
    cur.execute("SELECT * FROM domains;")
    domain_list = cur.fetchall()
    domain_name2id = {row[0] : str(row[1]) for row in domain_list}
    return domain_name2id

def split_morph_pos(morph):
    """
    splits morph into the 'pos' and 'morph' strings for db search
    """
    string2morph_id = get_morph_dict()
    if isinstance(morph, str) and morph != None:
        morph_list = morph.split(',')
        if morph_list[0] in string2morph_id.keys():
            pos = str(string2morph_id[morph_list[0]])
            try:
                morph_list = morph_list[1:]
                morph = '|'.join(morph_list)
            except IndexError:
                morph = ""
        else:
            pos = ""
    else:
        pos = ""
        morph = ""
    return pos, morph

def is_lemma_string(lemma):
    """
    check whether input lemma is a string
    """
    if isinstance(lemma, str):
        return lemma
    else:
        return ""

def get_extreme(extreme, range_minimum, range_maximum):
    """
    extreme : should be min or max
    range_minimum::int : minimum value you want your extreme to be 
    range_maximum::int : maximum value you want your extreme to be      
    """
    if isinstance(extreme, str):
        if extreme == "":
            extreme = range_minimum
        else:
            extreme = int(extreme)
            if extreme >= range_minimum and extreme <= range_maximum:
                extreme = int(extreme)
            elif extreme > range_maximum:
                extreme = range_maximum
            else:
                extreme = range_minimum        
    else:
        extreme = range_minimum
    return extreme

def get_values(lemma1, lemma2, morph1, morph2, min_, max_):

    lemma1 = is_lemma_string(lemma1)
    lemma2 = is_lemma_string(lemma2)

    pos1, morph1 = split_morph_pos(morph1)
    pos2, morph2 = split_morph_pos(morph2)
            
    # if isinstance(syntrole, str):
    #     syntrole = syntrole.split('-')[0]
    #     if syntrole in string2syntrole_id.keys():
    #         syntrole = str(string2syntrole_id[syntrole])
    #     else:
    #         syntrole = "_"
    # else:
    #     syntrole = "_"

    min_ = get_extreme(min_, 1, 4)
    max_ = get_extreme(max_, 1, 5)

    return lemma1, lemma2, pos1, pos2, morph1, morph2, min_, max_

# def check_syntrole(result, word, syntrole):

#     cur = CONN.cursor()
#     word1_word2_result = []

#     if syntrole != "_":
#         print("actually checking syntrole")
#         for line in result:
#             print(type(line[0]))
#             stmt = '''SELECT * FROM wordpairs
#                     WHERE synt_role_id = "''' + str(syntrole) + '''"
#                     AND head_id = ''' + str(word["id_word"]) + '''
#                     AND dependent_id = "''' + str(line[0]) + '''"
#                     ;'''
#             cur.execute(stmt)
#             res = cur.fetchall()
#             if res:
#                 result_dict = {"id_sent" : word["id_sent"], "id_text" : word["id_text"],  "word1" : word["id_word"], "word2" : line[0]}
#                 word1_word2_result.append(result_dict)
#             else:
#                 result_dict = {"id_sent" : 0, "id_text" : 0, "word1" : 0, "word2" : 0}
#                 word1_word2_result.append(result_dict)
#     else:
#         for line in result:
#             result_dict = {"id_sent" : word["id_sent"], "id_text" : word["id_text"], "word1" : word["id_word"], "word2" : line[0]}
#             word1_word2_result.append(result_dict)
#    return word1_word2_result

def generate_sent(result):
    """
    result : list of tuples,
    where tuple position are:
    0- list of words::(str or int) to boldify, 1- sentence_id::str, 2- text_id::str, 
    3- author::str, 4- year::str, 5- title::str, 6- id_domain::int
    """
    cur = CONN.cursor()
    id2domain = get_id2domain_dictionary()
    sents = list()
    for result_tuple in result:

        ## MAIN PARAGRAPH
        stmt = f"SELECT id_word, word FROM words WHERE id_sent = {result_tuple[1]} AND id_text = {result_tuple[2]};"
        cur.execute(stmt)
        main_paragraph = cur.fetchall()
        main_paragraph = stringify_sent(main_paragraph, result_tuple[0])

        ## 1st PARAGRAPH
        stmt = f"SELECT id_word, word FROM words WHERE id_sent = {str(int(result_tuple[1]) - 1)} AND id_text = {result_tuple[2]};"
        cur.execute(stmt)
        first_paragraph = cur.fetchall()
        first_paragraph = stringify_sent(first_paragraph, result_tuple[0])

        ## LAST PARAGRAPH
        stmt = f"SELECT id_word, word FROM words WHERE id_sent = {str(int(result_tuple[1]) + 1)} AND id_text = {result_tuple[2]};"
        cur.execute(stmt)
        last_paragraph = cur.fetchall()
        last_paragraph = stringify_sent(last_paragraph, result_tuple[0])

        ## REFERENCE
        reference = f"{result_tuple[3]}, {result_tuple[4]}, {result_tuple[5]} - Домен: {id2domain.get(result_tuple[6])}"
        
        sent = (first_paragraph, main_paragraph, last_paragraph, reference)
        if sent:
            sents.append(sent)
    return sents

def get_words4lemma(lemma, morph, pos, frequency):
    cur = CONN.cursor()
    word_id_list = list()

    if lemma:
        stmt = """SELECT tab1.id_unigram FROM (    
                                    SELECT temp.id_unigram, temp.unigram, pos, morph, """ + frequency + """ FROM  
                                    (SELECT t.*,  @row_num :=@row_num + 1 AS row_num FROM unigrams t,      
                                    (SELECT @row_num:=0) counter ORDER BY """ + frequency + """) temp
                                    INNER JOIN unitags tags ON temp.id_unigram = tags.id_unigram
                                    WHERE temp.original_cat = 1
                                    AND temp.row_num >= ROUND (.95* @row_num) 
                                    AND temp.unigram = %s
                                    AND temp.morph LIKE '%{}%'
                                    ORDER BY """ + frequency + """ DESC
                                    ) AS tab1
                                        INNER JOIN pos pos ON tab1.pos = pos.pos """
        if pos:
            stmt += f"WHERE pos.id_pos = {pos}"
        stmt += "LIMIT 10;"
        stmt_word = stmt.format(morph)
        cur.execute(stmt_word, (lemma, ))
        result = cur.fetchall()
        print(result)
        for id_unigram in result:

            sub_stmt = """SELECT w.id_word, w.id_sent, w.id_text, meta.author, meta.year, meta.title, meta.id_domain FROM 
                    (SELECT id_sent, id_word, id_text
                    FROM words  
                    WHERE id_unigram = """ + str(id_unigram[0]) + """) AS w 
                        JOIN metadata meta ON w.id_text = meta.id_text
                    ORDER BY RAND()
                    LIMIT 50;"""
            cur.execute(sub_stmt)
            result = cur.fetchall()
        return result
    else:
        print("NO LEMMA")
        return None

def get_frequency(search_domain):
    domain_name2id = get_domain_dictionary()
    domain = domain_name2id.get(search_domain)

    if domain:
        return f'freq{domain}'
    else:   
        return 'freq_all'

def lemma_search(lemma1, lemma2, morph1, morph2, min_, max_, domain):

    lemma1, lemma2, pos1, pos2, morph1, morph2, min_, max_ = get_values(lemma1, lemma2, morph1, morph2, min_, max_)

    cur = CONN.cursor()

    row_headers = ["Примерные предложения"]
    frequency = get_frequency(domain)

    word1_id_list = get_words4lemma(lemma1, morph1, pos1, frequency)
    word2_id_list = get_words4lemma(lemma2, morph2, pos2, frequency)
    sent_list = list()

    # INNER JOIN unigrams uni ON word_tab.id_unigram = uni.id_unigram
    if word1_id_list and word2_id_list and lemma1 and lemma2:
        for word1 in word1_id_list:
            word1_id = word1[0]
            id_sent = str(word1[1])
            id_text = str(word1[2])

            i = 0
            for word2 in word2_id_list:
                if i < 25:
                    word2_id = word2[0]
                    id_sent2 = str(word2[1])
                    author = str(word1[3])
                    year = str(word1[4])
                    title = str(word1[5])
                    id_domain = word1[6]
                    if id_sent == id_sent2 and word2_id >= word1_id + min_ and word2_id <= word1_id + max_:
                        i += 1
                        stmt = """SELECT word_tab.id_word FROM
                            (SELECT id_word, id_unigram FROM words WHERE id_word >= {}
                            AND id_word <= {}
                            AND id_sent = {}
                            AND id_text = {}) AS word_tab
                                INNER JOIN unigrams uni ON word_tab.id_unigram = uni.id_unigram
                                INNER JOIN unitags tags ON uni.id_unigram = tags.id_unigram
                                INNER JOIN pos pos ON tags.pos = pos.pos 
                            WHERE uni.original_cat = 1 
                            AND morph LIKE '%{}%'
                            AND uni.unigram <> "" """
                        if pos2:
                            stmt += f"AND pos.id_pos = {pos2} "
                        stmt += "ORDER BY uni." + frequency + " DESC LIMIT 50;"
                        stmt_word1 = stmt.format(str(word1_id + min_), str(word1_id + max_), id_sent, id_text, pos2, morph2)
                        cur.execute(stmt_word1)
                        result = cur.fetchall()
                        # word1_word2_result = check_syntrole(result, word1, syntrole)
                        word1_word2_result = [([word1_id, word2_id[0], ], id_sent, id_text, author, year, title, id_domain, ) for word2_id in result]
                        sents = generate_sent(word1_word2_result)
                        sent_list.extend(sents)
                else:
                    break

    # INNER JOIN unigrams uni ON word_tab.id_unigram = uni.id_unigram
    elif word1_id_list and not lemma2:
        for word1 in word1_id_list:
            word1_id = word1[0]
            id_sent = str(word1[1])
            id_text = str(word1[2])
            author = str(word1[3])
            year = str(word1[4])
            title = str(word1[5])
            id_domain = word1[6]
            stmt = """SELECT word_tab.id_word, uni.""" + frequency + """ FROM
                            (SELECT id_word, id_unigram FROM words WHERE id_word >= {}
                            AND id_word <= {}
                            AND id_sent = {}
                            AND id_text = {}) AS word_tab
                                INNER JOIN unigrams uni ON word_tab.id_unigram = uni.id_unigram
                                INNER JOIN unitags tags ON uni.id_unigram = tags.id_unigram
                                INNER JOIN pos pos ON tags.pos = pos.pos
                            WHERE uni.original_cat = 1
                            AND uni.unigram <> "" 
                            AND morph LIKE '%{}%' """
            if pos2:
                stmt += f"AND pos.id_pos = {pos2} "
            stmt += "ORDER BY uni." + frequency + " DESC LIMIT 100;"
            stmt_word1 = stmt.format(str(word1_id + min_), str(word1_id + max_), id_sent, id_text, morph2)
            cur.execute(stmt_word1)
            result = cur.fetchall()
            # word1_word2_result = check_syntrole(result, word1, syntrole)
            word1_word2_result = [([word1_id, word2_id[0], ], id_sent, id_text, author, year, title, id_domain ) for word2_id in result]
            sents = generate_sent(word1_word2_result)
            sent_list.extend(sents)

    # INNER JOIN unigrams uni ON word_tab.id_unigram = uni.id_unigram
    elif word2_id_list and not lemma1:
        for word2 in word2_id_list:
            word2_id = word2[0]
            id_sent = str(word2[1])
            id_text = str(word2[2])
            author = str(word2[3])
            year = str(word2[4])
            title = str(word2[5])
            id_domain = word2[6]
            stmt = """SELECT word_tab.id_word FROM
                            (SELECT id_word, id_unigram FROM words WHERE id_word >= {}
                            AND id_word <= {}
                            AND id_sent = {}
                            AND id_text = {}) AS word_tab
                                INNER JOIN unigrams uni ON word_tab.id_unigram = uni.id_unigram
                                INNER JOIN unitags tags ON uni.id_unigram = tags.id_unigram
                                INNER JOIN pos pos ON tags.pos = pos.pos
                            WHERE uni.original_cat = 1
                            AND uni.unigram <> "" 
                            AND morph LIKE '%{}%' """
            if pos1:
                stmt += f"AND pos.id_pos = {pos1} "
            stmt += "ORDER BY uni." + frequency + " DESC LIMIT 100;"
            stmt_word2 = stmt.format(str(word2_id - max_), str(word2_id - min_), id_sent, id_text, morph1)
            cur.execute(stmt_word2)
            result = cur.fetchall()
            # word1_word2_result = check_syntrole(result, word2, syntrole)
            word1_word2_result = [([word1_id[0], word2_id, ], id_sent, id_text, author, year, title, id_domain, ) for word1_id in result]
            sents = generate_sent(word1_word2_result)
            sent_list.extend(sents)
    else:
        sent_list.append((" --- ", "Введите хотя бы одно слово", " --- ", ""))
        row_headers = ["Повторите поиск"]

    json_data = []
    for sent in sent_list:
        json_data.append(dict(zip(row_headers, [sent])))
    
    return json_data

def single_token_search(search_token, search_domain):
    """
    search sentences containing input lemma
    search token : input token
    """

    if search_token:
        frequency = get_frequency(search_domain)

        cur = CONN.cursor()
        stmt = """SELECT unigram, id_unigram, """ + frequency + """ FROM  
        (SELECT t.*,  @row_num :=@row_num + 1 AS row_num FROM unigrams t,      
        (SELECT @row_num:=0) counter ORDER BY """ + frequency + """) temp 
        WHERE temp.original_cat = 1
        AND temp.row_num >= ROUND (.95* @row_num) 
        AND temp.unigram = %s
        ORDER BY """ + frequency + """ DESC;"""

        cur.execute(stmt, (search_token, ))

        list_id_unigram = cur.fetchall()
        dict_unigram_sent = {elem[1] : [] for elem in list_id_unigram}

        stmt = """SELECT COUNT(DISTINCT id_text) FROM words WHERE id_unigram in (""" + ', '.join(str(key) for key in dict_unigram_sent.keys()) + """);"""
        cur.execute(stmt)
        text_count = cur.fetchall()
        text_count = text_count[0][0]

        full_list_sentences = list()
        for id_unigram in dict_unigram_sent.keys():

            stmt = """SELECT w.id_word, w.id_sent, w.id_text, meta.author, meta.year, meta.title, meta.id_domain FROM 
                    (SELECT id_sent, id_word, id_text
                    FROM words  
                    WHERE id_unigram = """ + str(id_unigram) + """) AS w 
                        JOIN metadata meta ON w.id_text = meta.id_text
                    ORDER BY RAND()
                    LIMIT 5;"""
            cur.execute(stmt)
            list_id_sent = cur.fetchall()
            list_id_sent = [([sent[0], ], sent[1], sent[2], sent[3], sent[4], sent[5], sent[6], ) for sent in list_id_sent]
            full_list_sentences.extend(list_id_sent)
            
        sents = generate_sent(full_list_sentences)

        row_headers = [f"Примерные предложения, количестко найденных текстов: {text_count} (мы показываем только их часть)"]
        json_data = []
        for sent in sents:
            json_data.append(dict(zip(row_headers, [sent])))
        
        return json_data
    else:
        row_headers = ["Повторите поиск"]
        json_data = []
        sent_list = list()
        sent_list.append((" --- ", "Введите хотя бы одно слово", " --- ", ""))
        for sent in sent_list:
            json_data.append(dict(zip(row_headers, [sent])))
        
        return json_data

def stringify_sent(sent_db_result, words_to_boldify):
    sent = ["<strong>" + word[1] + "</strong>" if word[0] in words_to_boldify else word[1] for word in sent_db_result]
    sent = ''.join([('' if c in string.punctuation and c != "(" else ' ')+c for c in sent]).strip()
    sent = re.sub('^[{}]\s+'.format(string.punctuation), '', sent)
    sent = re.sub('(?<=\()\s', '', sent)
    sent += " "
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
        WHERE unigrams.original_cat = 1 AND unigrams.unigram = %s) as tab2
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

def collocation_search_test(search_token, search_metric, search_domain, ngrams=2):
    """
    produces list of most common bigram according to the first collocate (input by user);
    search_token : user input word
    search_metric : user selected metric for result sorting
    search_domain : user selected domain of search
    """
    cur = CONN.cursor()

    domain_name2id = get_domain_dictionary()

    if search_metric in ['frequency', 'pmi', 'logdice', 't_score']:

        domain = domain_name2id.get(search_domain)

        if domain:
            frequency = f'freq{domain}'
            if search_metric == 'frequency':
                orderby = f'd{domain}_freq'
            elif search_metric == 'pmi':
                orderby = f'd{domain}_pmi'
            elif search_metric == 'logdice':
                orderby = f'd{domain}_logdice'
            else:
                orderby = f'd{domain}_tsc'

        else:   
            frequency = 'freq_all'
            if search_metric == 'frequency':
                orderby = 'raw_frequency'
            elif search_metric == 'pmi':
                orderby = 'pmi'
            elif search_metric == 'logdice':
                orderby = 'tscore'
            else:
                orderby = 'logdice'

        ## UNIGRAMS
        stmt = """SELECT unigram, id_unigram, """ + frequency + """ FROM  
                (SELECT t.*,  @row_num :=@row_num + 1 AS row_num FROM unigrams t,      
                (SELECT @row_num:=0) counter ORDER BY """ + frequency + """) temp 
                WHERE temp.original_cat = 1
                AND temp.row_num >= ROUND (.95* @row_num) 
                AND temp.unigram = %s
                ORDER BY """ + frequency + """ DESC;"""

        cur.execute(stmt, (search_token, ))
        result = cur.fetchall()
        unigrams = ', '.join([line[0] for line in result])

        ## BIGRAMS 
        if ngrams == 2:
            stmt = """SELECT uni1.unigram, uni2.unigram FROM 
                    (SELECT t.*,  @row_num :=@row_num + 1 AS row_num FROM 2grams t, 
                        (SELECT @row_num:=0) counter  
                        WHERE t.wordform_1 in (""" + unigrams + """) 
                        OR t.wordform_2 in (""" + unigrams + """)
                        ORDER BY """ + orderby + """) 
                    temp 
                    INNER JOIN unigrams uni1 ON uni1.id_unigram = wordform_1
                    INNER JOIN unigrams uni2 ON uni2.id_unigram = wordform_2
                    WHERE temp.row_num >= ROUND (.995* @row_num)
                    AND uni1.original_cat = 1
                    AND uni2.original_cat = 1
                    ORDER BY """ + orderby + """ DESC;"""
            cur.execute(stmt)
            row_headers = [x[0] for x in cur.description]
            rv = cur.fetchall()

        ## TRIGRAMS
        elif ngrams == 3:
            stmt = """SELECT uni1.unigram, uni2.unigram, uni3.unigram FROM 
                      (SELECT t.*,  @row_num :=@row_num + 1 AS row_num FROM (
                          SELECT w1, w2, w3, """ + orderby + """ 
                          FROM 3grams_tokens 
                          JOIN 3grams ON 3grams.id_trigram = 3grams_tokens.id_trigram 
                          WHERE w1 in (""" + unigrams + """)
                          OR w2 in (""" + unigrams + """)
                          OR w3 in (""" + unigrams + """)
                          AND original_cat = 1 
                      ) t, 
                          (SELECT @row_num:=0) counter ORDER BY """ + orderby + """) 
                      temp 
                      INNER JOIN unigrams uni1 ON uni1.id_unigram = w1
                      INNER JOIN unigrams uni2 ON uni2.id_unigram = w2
                      INNER JOIN unigrams uni3 ON uni3.id_unigram = w3
                      WHERE temp.row_num >= ROUND (.995* @row_num)
                      ORDER BY """ + orderby + """ DESC;"""
            cur.execute(stmt)
            row_headers = [x[0] for x in cur.description]
            rv = cur.fetchall()

        # 4GRAMS
        elif ngrams == 4:
            stmt = """SELECT uni1.unigram, uni2.unigram, uni3.unigram, uni4.unigram, """ + orderby + """ FROM 
                      (SELECT t.*,  @row_num :=@row_num + 1 AS row_num FROM (
                          SELECT w1, w2, w3, w4, """ + orderby + """ 
                          FROM 4grams_tokens
                          JOIN 4grams ON 4grams.id_4gram = 4grams_tokens.id_4gram 
                          WHERE w1 in (""" + unigrams + """)
                          OR w2 in (""" + unigrams + """)
                          OR w3 in (""" + unigrams + """)
                          OR w4 in (""" + unigrams + """)
                          AND original_cat = 1
                      ) t, 
                          (SELECT @row_num:=0) counter ORDER BY """ + orderby + """) 
                      temp 
                      INNER JOIN unigrams uni1 ON uni1.id_unigram = w1
                      INNER JOIN unigrams uni2 ON uni2.id_unigram = w2
                      INNER JOIN unigrams uni3 ON uni3.id_unigram = w3
                      INNER JOIN unigrams uni4 ON uni4.id_unigram = w4
                      WHERE temp.row_num >= ROUND (.995* @row_num)
                      ORDER BY """ + orderby + """ DESC;"""
            cur.execute(stmt)
            row_headers = [x[0] for x in cur.description]
            rv = cur.fetchall()

        ## 5GRAMS
        elif ngrams == 5:
            stmt = """SELECT uni1.unigram, uni2.unigram, uni3.unigram, 
                      uni4.unigram, uni5.unigram, """ + orderby + """ FROM 
                      (SELECT t.*,  @row_num :=@row_num + 1 AS row_num FROM (
                          SELECT w1, w2, w3, w4, w5, """ + orderby + """ 
                          FROM 5grams_tokens
                          JOIN 5grams ON 5grams.id_5gram = 5grams_tokens.id_5gram 
                          WHERE w1 in (""" + unigrams + """)
                          OR w2 in (""" + unigrams + """)
                          OR w3 in (""" + unigrams + """)
                          OR w4 in (""" + unigrams + """)
                          OR w5 in (""" + unigrams + """)
                          AND original_cat = 1
                      ) t, 
                          (SELECT @row_num:=0) counter ORDER BY """ + orderby + """) 
                      temp 
                      INNER JOIN unigrams uni1 ON uni1.id_unigram = w1
                      INNER JOIN unigrams uni2 ON uni2.id_unigram = w2
                      INNER JOIN unigrams uni3 ON uni3.id_unigram = w3
                      INNER JOIN unigrams uni4 ON uni4.id_unigram = w4
                      INNER JOIN unigrams uni5 ON uni5.id_unigram = w5
                      WHERE temp.row_num >= ROUND (.995* @row_num)
                      ORDER BY """ + orderby + """ DESC;"""
            cur.execute(stmt)
            row_headers = [x[0] for x in cur.description]
            rv = cur.fetchall()

        elif ngrams == 6:
            stmt = """SELECT uni1.unigram, uni2.unigram, uni3.unigram,
                      uni4.unigram, uni5.unigram, uni6.unigram, """ + orderby + """ FROM 
                      (SELECT t.*,  @row_num :=@row_num + 1 AS row_num FROM (
                          SELECT w1, w2, w3, w4, w5, w6, """ + orderby + """ 
                          FROM 6grams_tokens
                          JOIN 6grams ON 6grams.id_6gram = 6grams_tokens.id_6gram 
                          WHERE w1 in (""" + unigrams + """)
                          OR w2 in (""" + unigrams + """)
                          OR w3 in (""" + unigrams + """)
                          OR w4 in (""" + unigrams + """)
                          OR w5 in (""" + unigrams + """)
                          OR w6 in (""" + unigrams + """)
                          AND original_cat = 1
                      ) t, 
                          (SELECT @row_num:=0) counter ORDER BY """ + orderby + """) 
                      temp 
                      INNER JOIN unigrams uni1 ON uni1.id_unigram = w1
                      INNER JOIN unigrams uni2 ON uni2.id_unigram = w2
                      INNER JOIN unigrams uni3 ON uni3.id_unigram = w3
                      INNER JOIN unigrams uni4 ON uni4.id_unigram = w4
                      INNER JOIN unigrams uni5 ON uni5.id_unigram = w5
                      INNER JOIN unigrams uni6 ON uni6.id_unigram = w6
                      WHERE temp.row_num >= ROUND (.995* @row_num)
                      ORDER BY """ + orderby + """ DESC;"""
            cur.execute(stmt)
            row_headers = [x[0] for x in cur.description]
            rv = cur.fetchall()
        else: 
            return ['']

        if row_headers and rv:   
            json_data = []
            for result in rv:
                json_data.append(dict(zip(row_headers, result)))
                return json_data
        else:
            return ['']