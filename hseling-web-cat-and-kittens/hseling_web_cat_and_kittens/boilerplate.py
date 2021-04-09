def get_domain_dict():
    domain_tokens_dict = {'Linguistics' : 3, 'Sociology' : 6, 'History' : 5, 'Law' : 2, 'Psychology' : 4, 'Economics' : 1, 'All_corpus' : '_'}
    return domain_tokens_dict

def domain_to_index(search_domain):
    """
    Convert domain name into corresponding index
    """
    domain_tokens_dict = get_domain_dict()

    if search_domain == 'Лингвистика':
        domain_token = domain_tokens_dict.get('Linguistics')
    elif search_domain == 'Социология':
        domain_token = domain_tokens_dict.get('Sociology')
    elif search_domain == 'История':
        domain_token = domain_tokens_dict.get('History')
    elif search_domain == 'Юриспруденция':
        domain_token = domain_tokens_dict.get('Law')
    elif search_domain == 'Психология и педагогика':
        domain_token = domain_tokens_dict.get('Psychology')
    elif search_domain == 'Экономика':
        domain_token = domain_tokens_dict.get('Economics')
    elif search_domain == 'Весь корпус':
        domain_token = domain_tokens_dict.get('All_corpus')
    else:
        domain_token = False
    return domain_token

def get_metric_dict():
    metric_dict = {'PMI' : 'pmi', 't-score' : 't_score', 'logdice' : 'logdice', 'Частота' : 'frequency'}
    return metric_dict

def metric_converter(search_metric):
    """
    converts metric string name into server-readable string
    """
    metric_dict = get_metric_dict()

    if search_metric == 'PMI':
        metric_token = metric_dict.get('PMI')
    elif search_metric == 't-score':
        metric_token = metric_dict.get('t-score')
    elif search_metric == 'logdice':
        metric_token = metric_dict.get('logdice')
    else:
        metric_token = 'frequency'
    
    return metric_token

def get_ngrams_dict():
    ngrams_dict = {"Биграммы" : 2, "Триграммы" : 3, "Четырехграммы" : 4, "Пятиграммы" : 5, "Шестиграммы" : 6}
    return ngrams_dict

def ngrams_converter(search_ngrams):
    """
    converts ngram string name into server-readable int
    """
    ngrams_dict = get_ngrams_dict()

    if search_ngrams == 'Биграммы':
        ngrams_token = ngrams_dict.get('Биграммы')
    elif search_ngrams == 'Триграммы':
        ngrams_token = ngrams_dict.get('Триграммы')
    elif search_ngrams == 'Четырехграммы':
        ngrams_token = ngrams_dict.get('Четырехграммы')
    elif search_ngrams == 'Пятиграммы':
        ngrams_token = ngrams_dict.get('Пятиграммы')
    else:
        ngrams_token = ngrams_dict.get('Шестиграммы') 
    
    return ngrams_token 
