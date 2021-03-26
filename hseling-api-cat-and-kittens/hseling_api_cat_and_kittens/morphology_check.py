import mysql.connector
import pandas as pd
import os
import re
import time
from random import randint, uniform
from conllu import parse, parse_tree

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

class Tagset:
    def __init__(self, unigram, lemm, morph, pos, start_id, end_id):
        self.unigram = unigram
        self.lemm = lemm
        self.morph = morph
        self.pos = pos
        self.start_id = start_id
        self.end_id = end_id

    def morph_to_string(self):
        if self.morph:
            subtaglist = list()
            for tag_element in list(self.morph.items()):
                subtag = '{}={}|'.format(tag_element[0], tag_element[1])
                subtaglist.append(subtag)

            fulltag = ''.join([str(x) for x in subtaglist])
            morph_string = fulltag[:-1]
            return morph_string
        else:
            morph_string = 'None'
            return morph_string
    
    def to_dict(self):
        return dict([('unigram', self.unigram), ('lemm', self.lemm), ('morph', self.morph), \
            ('pos', self.pos), ('start_id', self.start_id), ('end_id', self.end_id)])


def parser(conllu):
    """
    Yields a sentence from conllu tree with its tags

    """
    tree = parse(conllu)

    for token in tree:
        yield token


def get_words(conllu):
    """
    tree - generator of sentences (TokenLists) from conllu tree
    txtfile - txt version of the conllu file

    words, list is a list of all tokens we need from the tree
    size, int is a number of all words in the domain
    """

    words = []

    conllu_sents = parse(conllu)

    for sentence in conllu_sents:
        for token in sentence:
            token_range = token['misc']['TokenRange']
            start, end = token_range.split(':')
            token['start_id'], token['end_id'] = int(start), int(end)

            if token['form'] != '_' and token['upostag'] != '_' and token['upostag']!='NONLEX' and token['form'] not in r'[]\/':
                for unigram in token['form'].split(): # .lower()
                    words.append((unigram, token['lemma'], token['feats'], token['upostag'],
                    token['start_id'], token['end_id']))

    size = len(words)
    return words, size

def tagset_lemma(words):
    """
    Expands OrderedDict object to string
    words: list of tuples (unigram, lemm, morph, pos, start_id, end_id)
    """
    print('tagset being created...')
    word_list = list()
    for word in words:
        tagset = Tagset(*word)
        tagset.morph = tagset.morph_to_string()
        tagset = tagset.to_dict()
        word_list.append(tagset)
    return word_list


def morph_error_catcher(words, con=CONN, stop=STOPS, num=NUMBERS, lat=LATINS, cyr=CYRILLIC):
    mistakes = {}
    corrects = {}
    cur = con.cursor(dictionary=True, buffered=True)
    for i, word in enumerate(words):
        if word['unigram'].lower() not in punctuation and word['unigram'].lower() not in stop and \
        not num.match(word['unigram'].lower()) and not lat.search(word['unigram'].lower()) and \
        not cyr.search(word['unigram'].lower()) and word['pos'] != 'PROPN':

            time.sleep(uniform(0.2, 0.6))

            cur.execute("""SELECT unigram, lemm, morph, pos FROM
                        (SELECT unigram, morph, lemma FROM unigrams) AS a JOIN
                        (SELECT id_lemmas, id_pos, lemma AS lemm FROM lemmas) AS b ON lemma = id_lemmas JOIN pos ON b.id_pos = pos.id_pos
                        WHERE unigram="{}" &&
                        lemm="{}" &&
                        morph="{}" &&
                        pos="{}";""".format(word['unigram'], word['lemm'], word['morph'], word['pos']))

            rows = cur.fetchall()
            if not rows:
                mistakes[i] = word
            else:
                corrects[i] = word
    return mistakes, corrects


def correction(conllu, con=CONN):
    '''
    conllu: path to conllu format file or conllu data
    text: variable open in 'r' mode
    corrected_files_directory: directory path where the corrected txt file should end up
    print_correction = flag in to get a txt file with correction in the destination directory
    '''

    # tagset creation
    words, _ = get_words(conllu)
    tagset = tagset_lemma(words)
    mistakes, _ = morph_error_catcher(tagset, con)
    mistakes_list = mistakes.values()

    return list(mistakes_list)


def main():
    
    print('none')

if __name__ == "__main__":
    main()