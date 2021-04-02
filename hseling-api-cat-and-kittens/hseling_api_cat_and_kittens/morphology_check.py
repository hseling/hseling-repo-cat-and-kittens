import mysql.connector
import pandas as pd
import os
import re
import time
from random import randint, uniform
from conllu import parse, parse_tree
import json
import collections

from hseling_api_cat_and_kittens import boilerplate

from string import punctuation
punctuation += '«»—…“”–•'
PUNCT = set(punctuation)
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
STOPS = stopwords.words('russian')

NUMBERS = re.compile("[0-9]")
LATINS = re.compile(r"([a-zA-Z]+\W+)|(\W+[a-zA-Z]+)|(\W+[a-zA-Z]\W+)|([a-zA-Z]+)")
CYRILLIC = re.compile(r"([а-яА-ЯёЁ]+\W+)|(\W+[а-яА-ЯёЁ]+)|(\W+[а-яА-ЯёЁ]\W+)")

CONN = boilerplate.get_mysql_connection()

CASHING_PREFIX = 'cashing/'
MOST_COMMON_JSON = 'morphology_checking_most_common.json'
CASH_LIMIT = 5000

PATH_TO_MOST_COMMON_JSON = boilerplate.PATH_TO_DATA + CASHING_PREFIX + MOST_COMMON_JSON
MOST_COMMON_CORPUS = json.load(open(PATH_TO_MOST_COMMON_JSON, encoding='utf-8'))
MOST_COMMON_CORPUS = {token:set(known_parsing_results) for token, known_parsing_results in MOST_COMMON_CORPUS.items()}


def stringify_grammar(conllu_token):
    return '_'.join([conllu_token['lemma'], conllu_token['upos'], str(conllu_token['feats'])])

def stringify_morph(morph):
    if morph:
        subtaglist = list()
        for tag_element in list(morph.items()):
            subtag = '{}={}|'.format(tag_element[0], tag_element[1])
            subtaglist.append(subtag)

        fulltag = ''.join([str(x) for x in subtaglist])
        morph_string = fulltag[:-1]
        return morph_string
    return 'None'

class GrammarCash():
    def __init__(self, cash=None, cash_limit=5000):
        if cash:
            self.cash=cash
        else:
            self.cash = collections.defaultdict(set)
        self.cash_limit = max(cash_limit, len(self.cash))

    def __contains__(self, token):
        form = token['form']
        return form in self.cash and self.stringify_grammar(token) in self.cash[form]

    def add(self, token):
        stringified_grammar_tags = self.stringify_grammar(token)
        self.cash[token['form']].add(stringified_grammar_tags)
        if len(self.cash) > self.cash_limit:
            self.clean_cash()

    # def strict_check(self, token):
    #     form = token['form']
    #     if form in self.cash:
    #         if self.stringify_grammar(token) in self.cash[form]:
    #             return True
    #         else:
    #             return False
    #     else:
    #         return None

    def strict_check(self, token):
        form = token['form']
        if form in self.cash and self.stringify_grammar(token) in self.cash[form]:
            return True
        else:
            return False

    def clean_cash(self):
        self.cash = collections.defaultdict(set)

    def stringify_grammar(self, conllu_token):
        return '_'.join([conllu_token['lemma'], conllu_token['upos'], str(conllu_token['feats'])])


CORPUS_CASH = GrammarCash(cash=MOST_COMMON_CORPUS)
# CORPUS_CASH = GrammarCash(cash_limit=CASH_LIMIT)
CORRECT_CASH = GrammarCash(cash_limit=CASH_LIMIT)
WRONG_CASH = GrammarCash(cash_limit=CASH_LIMIT)



def is_morphology_correct(words, corpus_cash=CORPUS_CASH, correct_cash=CORRECT_CASH, wrong_cash=WRONG_CASH):
    mistakes_list = list()
    for token in words:
        if corpus_cash.strict_check(token) or correct_cash.strict_check(token):
           continue
        elif wrong_cash.strict_check(token):
           mistakes_list.append(token)
        else:
            database_query_result = morph_error_catcher(token)
            if database_query_result:
                correct_cash.add(token)
                print("cashing correct")
            else:
                mistakes_list.append(token)
                wrong_cash.add(token)
                print("cashing wrong")
    return mistakes_list

def get_words(conllu_sents):
    """
    tree - generator of sentences (TokenLists) from conllu tree
    txtfile - txt version of the conllu file

    words, list is a list of all tokens we need from the tree
    size, int is a number of all words in the domain
    """

    words = list()

    for sentence in conllu_sents:
        for token in sentence:
            if token['form'] != '_' and token['upos'] != '_' and token['upos'] != 'NONLEX' and token['form'] not in r'[]\/':
                for unigram in token['form'].split():
                    words.append(token)

    size = len(words)
    return words, size

def morph_error_catcher(token, con=CONN, stop=STOPS, num=NUMBERS, lat=LATINS, cyr=CYRILLIC):
    cur = con.cursor(dictionary=True, buffered=True)
    if token['form'].lower() not in punctuation and token['form'].lower() not in stop and \
    not num.match(token['form'].lower()) and not lat.search(token['form'].lower()) and \
    not cyr.search(token['form'].lower()) and token['upos'] != 'PROPN':
        morph = stringify_morph(token['feats'])
        cur.execute("""SELECT unigram, lemm, morph, pos FROM
                    (SELECT unigram, morph, lemma FROM unigrams) AS a JOIN
                    (SELECT id_lemmas, id_pos, lemma AS lemm FROM lemmas) AS b ON lemma = id_lemmas JOIN pos ON b.id_pos = pos.id_pos
                    WHERE unigram="{}" &&
                    lemm="{}" &&
                    morph="{}" &&
                    pos="{}";""".format(token['form'], token['lemma'], morph, token['upos']))

        rows = cur.fetchall()
        return rows
    return False


def correction(conllu_sents, con=CONN):
    '''
    conllu: path to conllu format file or conllu data
    text: variable open in 'r' mode
    corrected_files_directory: directory path where the corrected txt file should end up
    print_correction = flag in to get a txt file with correction in the destination directory
    '''

    words, _ = get_words(conllu_sents)
    mistakes_list = is_morphology_correct(words)
    mistake_ids = list()
    for mistake in mistakes_list:
        token_range = mistake['misc']['TokenRange']
        start, end = token_range.split(':')
        mistake_ids.append({ 'bos': int(start), 'end': int(end) })
    return mistake_ids
