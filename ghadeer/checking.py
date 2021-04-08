from morphology_check import *
from difflib import SequenceMatcher
import re

def morphology_checker(text):
    mistakes = correction(text)
    print(mistakes)
    if isinstance(mistakes, list):
        mistakes_ids = [ { 'bos': line['start_id'], 'end': line['end_id'] } for line in mistakes ]
        print(mistakes_ids)
        return mistakes_ids
    else:
        print("Wrong datatype")

def result_normalizer(table):
  a = []
  for round in table:
    for square in round:
      for el in square:
        a.append(el)
  return a

def duplicates_checker(text):
  text = " ".join(re.split("\n", text))
  words = [word + " " for word in text.split(' ')]
  result = Levenshtein_distance(words, w_size=5)
  return result

def NormalizeMatchingBlocks(mb, bias_tar=0, bias_comp=0):
  data_x = []
  data_y = []
  for x in mb:
    data_x.append((x[0]+bias_tar, x[0]+x[2]+bias_tar))
    data_y.append((x[1]+bias_comp, x[1]+x[2]+bias_comp))
  
  return Squeeze(data_x), Squeeze(data_y)

def Squeeze(data):
  new_data = []
  new_el = data[0]
  for idx in range(len(data)-1):
    if new_el[1] == data[idx+1][0]:
      new_el = (new_el[0], data[idx+1][1])
    else:
      if new_el[0] != new_el[1]:
        new_data.append({"bos": new_el[0], "end": new_el[1]})
        new_el = data[idx+1]
  if new_el[0] != new_el[1]:
    new_data.append({"bos": new_el[0], "end": new_el[1]})

  return new_data

def Levenshtein_distance(tokens, w_size = 5):
  blocks = []
  table = []
  bias_tar = 0
  bias_comp = 0
  for x in range(len(tokens) - w_size):
    beg = w_size + x
    end = 2 * (w_size) + x

    target = "".join(tokens[x:w_size + x])
    bias_comp = bias_tar + len(target)

    while end < len(tokens):

      compare = "".join(tokens[beg:end])
      ratio = SequenceMatcher(None, target, compare).ratio()
      if ratio > 0.75:
        # mb = Levenshtein.matching_blocks(Levenshtein.editops(target, compare), target, compare)
        mb = [(m.a, m.b, m.size) for m in SequenceMatcher(None, target, compare).get_matching_blocks()]
        matched = ''.join([target[e[0]:e[0]+e[2]] for e in mb])
        blocks.append(matched)
        table.append(NormalizeMatchingBlocks(mb, bias_tar=bias_tar, bias_comp=bias_comp))
        bias_comp += len(''.join(tokens[beg:end][0]))
        beg += 1
        end += 1
      elif ratio > 0.4:
        bias_comp += len(''.join(tokens[beg:end][0]))
        beg += 1
        end += 1
      else:
        bias_comp += len("".join(tokens[beg:end]))
        beg += w_size
        end += w_size
    
    bias_tar += len(tokens[x:w_size + x][0])
  return result_normalizer(table)