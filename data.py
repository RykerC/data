import os
from collections import Counter
import xml.etree.ElementTree as ET

def _get_abs_pos(cur, ids):
  min_dist = 1000
  for i in ids:
    if abs(cur - i) < min_dist:
      min_dist = abs(cur - i)
  if min_dist == 1000:
    raise("[!] ids list is empty")
  return min_dist

def _count_pre_spaces(text):
  count = 0
  for i in xrange(len(text)):
    if text[i].isspace():
      count = count + 1
    else:
      break
  return count

def _count_mid_spaces(text, pos):
  count = 0
  for i in xrange(len(text) - pos):
    if text[pos + i].isspace():
      count = count + 1
    else:
      break
  return count

def _check_if_ranges_overlap(x1, x2, y1, y2):
  return x1 <= y2 and y1 <= x2

def _get_data_tuple(text, asp_term, label, word2idx):
  words = text.split()
  # Find the ids of aspect term
  fro = text.index(asp_term)
  to = fro + len(asp_term)
  ids, st, i = [], _count_pre_spaces(text), 0
  for word in words:
    if _check_if_ranges_overlap(st, st+len(word)-1, fro, to-1):
      ids.append(i)
    st = st + len(word) + _count_mid_spaces(text, st + len(word))
    i = i + 1
  pos_info, i = [], 0
  for word in words:
    pos_info.append(_get_abs_pos(i, ids))
    i = i + 1
  lab = None
  if label == -1:
    lab = 0
  elif label == 0:
    lab = 1
  else:
    lab = 2
  return pos_info, lab

def read_data(fname, source_count, source_word2idx, target_count, target_word2idx):
  if os.path.isfile(fname) == False:
    raise("[!] Data %s not found" % fname)

  tree = ET.parse(fname)
  root = tree.getroot()

  def getlocation(text, aspect):
    fro = text.index(aspect)
    to = fro + len(aspect)
    return fro, to


  source_words, target_words, max_sent_len = [], [], 0
  for Table1 in root:
    text = Table1.find('sentence').text.lower()
    source_words.extend(text.split())
    if len(text.split()) > max_sent_len:
      max_sent_len = len(text.split())
    for asp_terms in Table1.iter('aspects_seed'):
      for asp_term in asp_terms.findall('aspects_seed'):
        target_words.append(asp_term.lower())
  if len(source_count) == 0:
    source_count.append(['<pad>', 0])
  source_count.extend(Counter(source_words).most_common())
  target_count.extend(Counter(target_words).most_common())

  for word, _ in source_count:
    if word not in source_word2idx:
      source_word2idx[word] = len(source_word2idx)

  for word, _ in target_count:
    if word not in target_word2idx:
      target_word2idx[word] = len(target_word2idx)

  source_data, source_loc_data, target_data, target_label = list(), list(), list(), list()
  for Table1 in root:
    text = Table1.find('sentence').text.lower()
    fro, to = getlocation(text, Table1.iter('aspects_seed'))
    if len(text.strip()) != 0:
      idx = []
      for word in text.split():
        idx.append(source_word2idx[word])
      for asp_terms in Table1.iter('aspects_seed'):
        for asp_term in asp_terms.findall('aspects_seed'):
          source_data.append(idx)
          pos_info, lab = _get_data_tuple(text, asp_term.lower(), int(fro), int(to), Table1.iter('pol'), source_word2idx)
          source_loc_data.append(pos_info)
          target_data.append(target_word2idx[asp_term.lower()])
          target_label.append(lab)

  print("Read %s aspects from %s" % (len(source_data), fname))
  return source_data, source_loc_data, target_data, target_label, max_sent_len
