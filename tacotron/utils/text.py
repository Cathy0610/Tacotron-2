import re

# from . import cleaners
from .symbols import getSymbolSet, phonesplit

# Mappings from symbol to numeric ID and vice versa:
_cur_lang = None
_symbol_to_id = None
_id_to_symbol = None

def _change_lang(lang):
  global _cur_lang, _symbol_to_id, _id_to_symbol
  if _cur_lang != lang:
    _symbol_to_id = {s: i for i, s in enumerate(getSymbolSet(lang))}
    _id_to_symbol = {i: s for i, s in enumerate(getSymbolSet(lang))}
    _cur_lang = lang


# Regular expression matching text enclosed in curly braces:
_curly_re = re.compile(r'(.*?)\{(.+?)\}(.*)')


def text_to_sequence(text, cleaner_names, lang='zh'):
  '''Converts a string of text to a sequence of IDs corresponding to the symbols in the text.

    The text can optionally have ARPAbet sequences enclosed in curly braces embedded
    in it. For example, "Turn left on {HH AW1 S S T AH0 N} Street."

    Args:
      text: string to convert to a sequence
      cleaner_names: names of the cleaner functions to run the text through

    Returns:
      List of integers corresponding to the symbols in the text
  '''
  _change_lang(lang)

  sequence = []

  # text = _clean_text(text, cleaner_names)
  symbolsequence = text.split() if lang != 'en' else list(text)

  if lang == 'py2':
    for symbol in symbolsequence:
      # 1. tone annotation
      if symbol.isdigit():
        for idx in range(-1, -1-len(sequence), -1):
          if len(sequence[idx]) == 2:
            break
          else:
            sequence[idx].append(int(symbol))
      elif _should_keep_symbol(symbol):
        # 2. phoneme
        if symbol.isalpha():
          # 2.1 unvoiced phonemes
          if symbol in ['b', 'p', 'f', 'd', 't', 'g', 'k', 'h', 'j', 'q', 'x', 'zh', 'ch', 'sh', 'z', 'c', 's']:
            sequence.append([_symbol_to_id[symbol], 0])
          # 2.2 other phonemes
          else:
            sequence.append([_symbol_to_id[symbol]])
        # 3. prosodic struct
        else:
          sequence.append([_symbol_to_id[symbol], 0])
      elif len(symbol):
        raise NameError("unkown symbol name: %s" % symbol)
    return sequence

  
  if lang == 'cmu':
    symbolsequence = [symbol.rstrip('3') for symbol in symbolsequence]
  
  for s in symbolsequence:
    if _should_keep_symbol(s):
      sequence.append(_symbol_to_id[s])
    elif len(s):
      raise NameError("unkown phoneme name: %s" % s)

  # Check for curly braces and treat their contents as ARPAbet:
  # while len(text):
  #   m = _curly_re.match(text)
  #   if not m:
  #     sequence += _symbols_to_sequence(_clean_text(text, cleaner_names))
  #     break
  #   sequence += _symbols_to_sequence(_clean_text(m.group(1), cleaner_names))
  #   sequence += _arpabet_to_sequence(m.group(2))
  #   text = m.group(3)

  # Append EOS token
  sequence.append(_symbol_to_id['~'])
  sequence = [[i] for i in sequence]
  return sequence


def sequence_to_text(sequence, lang='zh'):
  '''Converts a sequence of IDs back to a string'''
  _change_lang(lang)
  result = ''
  for symbol_id in sequence:
    if symbol_id in _id_to_symbol:
      s = _id_to_symbol[symbol_id]
      # Enclose ARPAbet back in curly braces:
      if len(s) > 1 and s[0] == '@':
        s = '{%s}' % s[1:]
      result += s
  return result.replace('}{', ' ')


def _clean_text(text, cleaner_names):
  for name in cleaner_names:
    cleaner = getattr(cleaners, name)
    if not cleaner:
      raise Exception('Unknown cleaner: %s' % name)
    text = cleaner(text)
  return text


def _symbols_to_sequence(symbols):
  return [_symbol_to_id[s] for s in symbols if _should_keep_symbol(s)]

def _arpabet_to_sequence(text):
  return _symbols_to_sequence(['@' + s for s in text.split()])


def _should_keep_symbol(s):
  return s in _symbol_to_id and s is not '_' and s is not '~'
