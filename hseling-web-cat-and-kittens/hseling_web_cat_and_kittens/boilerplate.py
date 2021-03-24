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
    metric_dict = {'PMI' : 'pmi', 't-score' : 't_score', 'logdice' : 'logdice', 'Frequency' : 'frequency'}
    return metric_dict

def metric_converter(search_metric):
    """
    convert metric string name into server-readable string
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
