import requests
from nltk import sent_tokenize
from copy import copy

class ParagraphLengthException(Exception):
    def __init__(self, paragraph_length_limit):
        self.text = 'Too long paragraph is detected'
        self.paragraph_length_limit = paragraph_length_limit


class SpellChecker:
    def __init__(self, api_href='https://speller.yandex.net/services/spellservice.json/checkTexts', checker_limit=10000):
        self.__checker_limit = checker_limit
        self.__api_href = api_href
		
    def _checker_query(self, texts):
        response = requests.post(self.__api_href, {'text': texts})
        sucsess = response.status_code == 200
        problems = []
        if sucsess:
            problems = response.json()
           # print('получены результаты запроса')
        #print(problems)
        return problems, sucsess

    def check_spelling(self, text):
        paragraphs = text.split('\n')
        if all([len(paragraph) <= self.__checker_limit for paragraph in paragraphs]):
            problems, sucsess = self._split_and_check(paragraphs)
        else:
            raise ParagraphLengthException(self.__checker_limit)
       # print('все запросы выполнены')
        #print(problems)
        problems_with_context_and_fixed_ids = self.__add_context_and_fix_ids(problems, paragraphs)
        #print('все данные отформатированы')
        text_problems = []
        for paragraph_problems in problems_with_context_and_fixed_ids:
            text_problems += paragraph_problems
        return {'problems': text_problems, 'all_paragraphs_sucsess': sucsess}

    def _split_and_check(self, paragraphs):
        spelling_problems = []
        current_texts = []
        no_server_problems = True
        current_len = 0
        for i, text in enumerate(paragraphs):
            if current_len + len(text) > self.__checker_limit:
                current_text_problems, current_text_problems_status_is_200 = self._checker_query(current_texts)
                spelling_problems += current_text_problems
                no_server_problems *= current_text_problems_status_is_200
                current_len = len(text)
                current_texts = []
                current_texts.append(text)
            else:
                current_texts.append(text)
                current_len += len(text)
        current_text_problems, current_text_problems_status_is_200 = self._checker_query(current_texts)
        spelling_problems += current_text_problems
        no_server_problems *= current_text_problems_status_is_200 
        return spelling_problems, no_server_problems     

    def __add_context_and_fix_ids(self, paragraph_problems, paragraphs):
        current_beginning_id = 0
        for problems, paragraph in zip(paragraph_problems, paragraphs):
            if problems:
                sentences_with_id = self._get_sentences_with_id(paragraph)
               # print('получены айди предложений')
                current_sent_id = 0
                for problem in problems:
                    current_sent_data = sentences_with_id[current_sent_id]
                    current_sent = current_sent_data['sent']
                    while problem['pos'] > current_sent_data['end']:
                        current_sent_id += 1
                        current_sent_data = sentences_with_id[current_sent_id]
                        current_sent = current_sent_data['sent']
                    problem['context'] = current_sent
                    problem['pos'] += current_beginning_id
                    problem['end'] = problem['pos'] + problem['len']
                   # print('отформатирован абзац')
            current_beginning_id = current_beginning_id + len(paragraph) + 1
        return paragraph_problems

    def _get_sentences_with_id(self, text, splitting_threshold=70, lang='russian'):
        '''
        Splits text into shorter fragments
        '''
        if len(text) <= splitting_threshold:
            sents_with_ids = [{'sent': text, 'pos':0, 'end': len(text)-1}]
        else:
            sents = sent_tokenize(text, lang)
            #print(sents)
            sents_with_ids = []
            prev_text_len=0
            text_copy = copy(text)
           # print(text_copy)
            for sent in sents:
                #print(sent)
                sent_position_data = {'sent': sent}
                position = text_copy.find(sent)
               # print(position)
                sent_position_data['pos'] = prev_text_len + position
                sent_position_data['end'] = prev_text_len + position + len(sent)
                sents_with_ids.append(sent_position_data)
                text_copy = text_copy[position + len(sent):]
                prev_text_len = sent_position_data['end'] 
        return sents_with_ids


def make_changes(text, corrections, ignore_options=['не исправлять']):
    text = copy(text)
    corrections = sorted(corrections, reverse=True, key=lambda x: x['pos'])
    for correction in corrections:
        if correction['chosen_value'] not in ignore_options:
            text = text[:correction['pos']] + correction['chosen_value'] + text[correction['end']:]
    return  text