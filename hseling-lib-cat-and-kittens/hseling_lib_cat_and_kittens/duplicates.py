# from difflib import SequenceMatcher
# import re


# def result_normalizer(table):
#   a = []
#   for round in table:
#     for square in round:
#       for el in square:
#         a.append(el)
#   return a

# def check_duplicates(text):
#   text = " ".join(re.split("\n", text))
#   words = [word + " " for word in text.split(' ')]
#   result = Levenshtein_distance(words, w_size=5)
#   return result


# def NormalizeMatchingBlocks(mb, bias_tar=0, bias_comp=0):
#   data_x = []
#   data_y = []
#   for x in mb:
#     data_x.append((x[0]+bias_tar, x[0]+x[2]+bias_tar))
#     data_y.append((x[1]+bias_comp, x[1]+x[2]+bias_comp))

#   return Squeeze(data_x), Squeeze(data_y)

# def Squeeze(data):
#   new_data = []
#   new_el = data[0]
#   for idx in range(len(data)-1):
#     if new_el[1] == data[idx+1][0]:
#       new_el = (new_el[0], data[idx+1][1])
#     else:
#       if new_el[0] != new_el[1]:
#         new_data.append({"bos": new_el[0], "end": new_el[1]})
#         new_el = data[idx+1]
#   if new_el[0] != new_el[1]:
#     new_data.append({"bos": new_el[0], "end": new_el[1]})

#   return new_data

# def Levenshtein_distance(tokens, w_size = 5):
#   blocks = []
#   table = []
#   bias_tar = 0
#   bias_comp = 0
#   for x in range(len(tokens) - w_size):
#     beg = w_size + x
#     end = 2 * (w_size) + x

#     target = "".join(tokens[x:w_size + x])
#     bias_comp = bias_tar + len(target)

#     while end < len(tokens):

#       compare = "".join(tokens[beg:end])
#       ratio = SequenceMatcher(None, target, compare).ratio()
#       if ratio > 0.75:
#         # mb = Levenshtein.matching_blocks(Levenshtein.editops(target, compare), target, compare)
#         mb = [(m.a, m.b, m.size) for m in SequenceMatcher(None, target, compare).get_matching_blocks()]
#         matched = ''.join([target[e[0]:e[0]+e[2]] for e in mb])
#         blocks.append(matched)
#         table.append(NormalizeMatchingBlocks(mb, bias_tar=bias_tar, bias_comp=bias_comp))
#         bias_comp += len(''.join(tokens[beg:end][0]))
#         beg += 1
#         end += 1
#       elif ratio > 0.4:
#         bias_comp += len(''.join(tokens[beg:end][0]))
#         beg += 1
#         end += 1
#       else:
#         bias_comp += len("".join(tokens[beg:end]))
#         beg += w_size
#         end += w_size

#     bias_tar += len(tokens[x:w_size + x][0])
#   return result_normalizer(table)

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
  while (re.match('\s', text[end-1]) == None) and (end < len(text)):
    end += 1
  return beg, end

def check_duplicates(text):
  text = [line.rstrip() for line in text]
  text = " ".join(text)
  words = [word + " " for word in text.split(' ')]
  sentences = sent_tokenize(text)
  table = []
  for i in range(len(sentences)):
    windows = get_windows(sentences[i])
    for target in windows:
      for curr_sent in sentences[i+1:i+6]:
        pat=r'(?e)((?:%s){e<%i})'
        pat=pat % (target, int((len(target)+15)/5) - 1)
        m=regex.search(pat, curr_sent)
        if m:
          b = text.rfind(m.group(1))
          e = text.rfind(m.group(1)) + m.span(0)[1] - m.span(0)[0]
          right = find_space(text, b, e)
          table.append({'bos': right[0], 'end': right[1]})
          table.append({'bos': text.rfind(target), 'end': text.rfind(target)+len(target)})
  return table
