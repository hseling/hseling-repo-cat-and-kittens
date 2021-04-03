import regex
import re
import codecs
import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt')


def get_windows(l):
  a = []
  l_1 = re.split(' ', l)
  for i in range(0, len(l_1)-3, 1):
      a.append(' '.join(l_1[i:i+4]))
  return a

def find_space(text, beg, end):
  while (re.match('\s', text[beg-1]) == None) and (beg > 0):
    beg -= 1
  while (re.match('\s', text[end]) == None) and (end < len(text)):
    end += 1
  return beg, end

def check_duplicates(text):
  text = re.sub('\s+', ' ', text)
  words = [word + " " for word in text.split(' ')]
  sentences = sent_tokenize(text)
  table = []
  for i in range(len(sentences)):
    windows = get_windows(sentences[i])
    for target in windows:
      for curr_sent in sentences[i+1:i+4]:
        pat=r'(?e)((?:%s){e<%i:[а-я]})'
        pat=pat % (target, int((len(target)+15)/5) - 1)
        m=regex.search(pat, curr_sent)
        if m:
          b = text.rfind(m.group(1))
          e = text.rfind(m.group(1)) + m.span(0)[1] - m.span(0)[0]
          right = find_space(text, b, e)
          table.append({'bos': right[0], 'end': right[1]})
          table.append({'bos': text.rfind(target), 'end': text.rfind(target)+len(target)})
  return table
