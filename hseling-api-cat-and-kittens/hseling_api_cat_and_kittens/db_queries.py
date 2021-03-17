from hseling_api_cat_and_kittens import boilerplate

CONN = boilerplate.get_mysql_connection()

def bigram_search(search_token):
    '''
    get the best fitting bigram
    search_token : word input from user
    '''
    frequency = 'freq_all'
    cur = CONN.cursor()
    stmt = """SELECT unigrams.""" + frequency + """ as frequency, lemmas.lemma as lemma
    FROM unigrams 
    JOIN lemmas ON unigrams.lemma = lemmas.id_lemmas
    WHERE unigrams.unigram = %(src_token)s;"""
    cur.execute(stmt, {'src_token' : search_token})
    row_headers = [x[0] for x in cur.description]
    rv = cur.fetchall()
    json_data = []
    for result in rv:
        json_data.append(dict(zip(row_headers, result)))
    
    return json_data