from parsing import get_token_start, get_token_end

MORE_LESS = ['более', 'менее']


def find_genitive_chaines(conllu_sents, threshold=3, nouns_only=True):
    current_gen_chain = {}
    for sent in conllu_sents:
        gen_chains = []
        num_prev_gens = 0
        for token in sent:
            if token['upostag'] != 'PUNCT':
                if token['feats'] and 'Case' in token['feats'] and token['feats']['Case']=='Gen':
                    if 'bos' not in current_gen_chain:
                        current_gen_chain['bos'] = get_token_start(token)
                    current_gen_chain['end'] = get_token_end(token)
                    if token['upostag']=='NOUN' or not nouns_only:
                        num_prev_gens += 1    
                else:
                    if num_prev_gens >= threshold:
                        gen_chains.append(current_gen_chain)
                    current_gen_chain = {}
                    num_prev_gens = 0
        if num_prev_gens >= threshold:
            gen_chains.append(current_gen_chain)
    return gen_chains


def find_wrong_comparativ(conllu_sents):
    wrong_comparativs = []
    for sent in conllu_sents:
        for i, token in enumerate(sent[:-1]):
            if token['lemma'] in MORE_LESS:
                more_less_start = get_token_start(token)
                next_token = sent[i+1]
                if 'Degree' in next_token['feats'] and next_token['feats']['Degree'] != 'Pos':
                    wrong_comparative_end = get_token_end(next_token)
                    wrong_comparativs.append({'bos': more_less_start, 'end': wrong_comparative_end})
    return wrong_comparativs


def find_IvsWe_problems(conllu_sents, sort_problems=False):
    I_tokens = []
    We_tokens = []
    for sent in conllu_sents:
        I_tokens += sent.filter(lemma='я')
        We_tokens += sent.filter(lemma='мы')
    if I_tokens and We_tokens:
        problems = [{'bos': get_token_start(token), 'end': get_token_end(token)} for token in I_tokens+We_tokens]
        if sort_problems:
            problems = sorted(problems, key = lambda problem: problem['bos'])
        return problems
    else:
        return []




