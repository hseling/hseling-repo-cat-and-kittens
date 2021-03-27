import codecs, re
from nltk import sent_tokenize
import pandas as pd
from collections import Counter

vowels = ["а", "я", "о", "ё", "у", "ю", "е", "э", "ы", "и", "á", "ó"]

# Readability

def countASLandASW(text):
    text = re.split("\n", text)
    text = [line.rstrip() for line in text]
    joinedText = re.sub('́', "", " ".join(text))
    joinedText = re.sub(" -+ ", " ", " ".join(text))
    words = re.findall('[\dáóа-яё-]+', joinedText.lower())
    words = [word for word in words if word != "-"]
    word_num = len(words)
    
    syll_num = 0
    for word in words:
        for letter in set(word):
            if letter in vowels: 
                syll_num += 1
    
    sentences = sent_tokenize(joinedText, 'russian')
    sent_num = len(sentences)
    
    ASL = word_num/sent_num #average sent length
    ASW = syll_num/word_num #average num of syllables per word
    return (ASL, ASW)

def countFKG(text):
    ASL, ASW = countASLandASW(text)     
    FKG = 0.36 * ASL + 5.76 * ASW - 11.97
    return(FKG)

def uniqueWords(text):
    text = re.split("\n", text)
    text = [line.rstrip() for line in text]
    joinedText = re.sub('́', "", " ".join(text))
    joinedText = re.sub(" -+ ", " ", " ".join(text))
    words = re.findall('[\dáóа-яё-]+', joinedText.lower())
    words = [word for word in words if word != "-"]
    word_num = len(words)
    unique_word = len(set(words))
    return word_num, unique_word

def CEFR(FKG):
    if FKG >= 5.155:
        level = 'C2'
    elif FKG >= 4.57:
        level = 'C1'
    elif FKG >= 2.63:
        level = 'B2'
    elif FKG >= 2.31:
        level = 'B1'
    elif FKG >= 1.14:
        level = 'A2'
    elif FKG >= -0.48:
        level = 'A1'
    else: level = 'ваш уровень слишком низок'
    return level    