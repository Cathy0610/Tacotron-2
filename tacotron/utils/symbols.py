'''
Defines the set of symbols used in text input to the model.

The default is a set of ASCII characters that works well for English or text that has been run
through Unidecode. For other data, you can modify _characters. See TRAINING_DATA.md for details.
'''
from . import cmudict

_pad        = '_'
_eos        = '~'
_characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!\'\"(),-.:;? '

_sep = ' '
# _phone = [' ', \
#             'a1', 'a2', 'a3', 'a4', 'a5', \
#             'aa', \
#             'ai1', 'ai2', 'ai3', 'ai4', 'ai5', \
#             'an1', 'an2', 'an3', 'an4', 'an5', \
#             'ang1', 'ang2', 'ang3', 'ang4', 'ang5', \
#             'ao1', 'ao2', 'ao3', 'ao4', 'ao5', \
#             'b', 'c', 'ch', 'd', \
#             'e1', 'e2', 'e3', 'e4', 'e5', \
#             'ee', \
#             'ei1', 'ei2', 'ei3', 'ei4', 'ei5', \
#             'en1', 'en2', 'en3', 'en4', 'en5', \
#             'eng1', 'eng2', 'eng3', 'eng4', 'eng5', \
#             'er2', 'er3', 'er4', 'er5', \
#             'f', 'g', 'h', \
#             'i1', 'i2', 'i3', 'i4', 'i5', \
#             'ia1', 'ia2', 'ia3', 'ia4', 'ia5', \
#             'ian1', 'ian2', 'ian3', 'ian4', 'ian5', \
#             'iang1', 'iang2', 'iang3', 'iang4', 'iang5', \
#             'iao1', 'iao2', 'iao3', 'iao4', 'iao5', \
#             'ie1', 'ie2', 'ie3', 'ie4', 'ie5', \
#             'ii', \
#             'in1', 'in2', 'in3', 'in4', 'in5', \
#             'ing1', 'ing2', 'ing3', 'ing4', 'ing5', \
#             'iong1', 'iong2', 'iong3', 'iong4', 'iong5', \
#             'iu1', 'iu2', 'iu3', 'iu4', 'iu5', \
#             'ix1', 'ix2', 'ix3', 'ix4', 'ix5', \
#             'iy1', 'iy2', 'iy3', 'iy4', 'iy5', \
#             'iz4', 'iz5', \
#             'j', 'k', 'l', 'm', 'n', \
#             'o1', 'o2', 'o3', 'o4', 'o5', \
#             'ong1', 'ong2', 'ong3', 'ong4', 'ong5', \
#             'oo', \
#             'ou1', 'ou2', 'ou3', 'ou4', 'ou5', \
#             'p', 'q', 'r', 's', 'sh', 'sil', 't', \
#             'u1', 'u2', 'u3', 'u4', 'u5', \
#             'ua1', 'ua2', 'ua3', 'ua4', 'ua5', \
#             'uai1', 'uai2', 'uai3', 'uai4', 'uai5', \
#             'uan1', 'uan2', 'uan3', 'uan4', 'uan5', \
#             'uang1', 'uang2', 'uang3', 'uang4', 'uang5', \
#             'uen1', 'uen3', 'uen4', 'uen5', \
#             'ueng1', 'ueng3', 'ueng4', 'ueng5', \
#             'ui1', 'ui2', 'ui3', 'ui4', 'ui5', \
#             'un1', 'un2', 'un3', 'un4', 'un5', \
#             'uo1', 'uo2', 'uo3', 'uo4', 'uo5', \
#             'uu', \
#             'v1', 'v2', 'v3', 'v4', 'v5', \
#             'van1', 'van2', 'van3', 'van4', 'van5', \
#             've1', 've2', 've3', 've4', 've5', \
#             'vn1', 'vn2', 'vn3', 'vn4', 'vn5', \
#             'vv', 'w', 'x', 'y', 'z', 'zh']

_initials = ['b', 'p', 'f', 'm', \
            'd', 't', 'n', 'l', \
            'g', 'k', 'h', \
            'j', 'q', 'x', \
            'zh', 'ch', 'sh', 'r', \
            'z', 'c', 's', \
            'w', 'y']
_finals_net = ['a1', 'a2', 'a3', 'a4', 'a5', \
            'ai1', 'ai2', 'ai3', 'ai4', 'ai5', \
            'an1', 'an2', 'an3', 'an4', 'an5', \
            'ang1', 'ang2', 'ang3', 'ang4', 'ang5', \
            'ao1', 'ao2', 'ao3', 'ao4', 'ao5', \
            'e1', 'e2', 'e3', 'e4', 'e5', \
            'ei1', 'ei2', 'ei3', 'ei4', 'ei5', \
            'en1', 'en2', 'en3', 'en4', 'en5', \
            'eng1', 'eng2', 'eng3', 'eng4', 'eng5', \
            'er1', 'er2', 'er3', 'er4', 'er5', \
            'ev1', 'ev2', 'ev3', 'ev4', 'ev5', \
            'i1', 'i2', 'i3', 'i4', 'i5', \
            'ia1', 'ia2', 'ia3', 'ia4', 'ia5', \
            'ian1', 'ian2', 'ian3', 'ian4', 'ian5', \
            'iang1', 'iang2', 'iang3', 'iang4', 'iang5', \
            'iao1', 'iao2', 'iao3', 'iao4', 'iao5', \
            'ie1', 'ie2', 'ie3', 'ie4', 'ie5', \
            'in1', 'in2', 'in3', 'in4', 'in5', \
            'ing1', 'ing2', 'ing3', 'ing4', 'ing5', \
            'iong1', 'iong2', 'iong3', 'iong4', 'iong5', \
            'iou1', 'iou2', 'iou3', 'iou4', 'iou5', \
            'iu1', 'iu2', 'iu3', 'iu4', 'iu5', \
            'o1', 'o2', 'o3', 'o4', 'o5', \
            'ong1', 'ong2', 'ong3', 'ong4', 'ong5', \
            'ou1', 'ou2', 'ou3', 'ou4', 'ou5', \
            'u1', 'u2', 'u3', 'u4', 'u5', \
            'ua1', 'ua2', 'ua3', 'ua4', 'ua5', \
            'uai1', 'uai2', 'uai3', 'uai4', 'uai5', \
            'uan1', 'uan2', 'uan3', 'uan4', 'uan5', \
            'uang1', 'uang2', 'uang3', 'uang4', 'uang5', \
            'uei1', 'uei2', 'uei3', 'uei4', 'uei5', \
            'uen1', 'uen2', 'uen3', 'uen4', 'uen5', \
            'ueng1', 'ueng3', 'ueng3', 'ueng4', 'ueng5', \
            'ue1', 'ue2', 'ue3', 'ue4', 'ue5', \
            'ui1', 'ui2', 'ui3', 'ui4', 'ui5', \
            'un1', 'un2', 'un3', 'un4', 'un5', \
            'uo1', 'uo2', 'uo3', 'uo4', 'uo5', \
            'v1', 'v2', 'v3', 'v4', 'v5', \
            'van1', 'van2', 'van3', 'van4', 'van5', \
            've1', 've2', 've3', 've4', 've5', \
            'vn1', 'vn2', 'vn3', 'vn4', 'vn5']
_finals = []
for f in _finals_net:
    _finals += [f, f[:-1]+'r'+f[-1]]

def phonesplit(pinyin):
    # print(pinyin)
    if len(pinyin) > 1:
        if pinyin[:2] in _initials:
            return (pinyin[:2], pinyin[2:])
        elif pinyin[0] in _initials:
            return (pinyin[0], pinyin[1:])
        else:
            return ('', pinyin)
    else:
        raise NameError('Invalid pinyin: %s' % pinyin)

# Prepend "@" to ARPAbet symbols to ensure uniqueness (some are the same as uppercase letters):
#_arpabet = ['@' + s for s in cmudict.valid_symbols]

# Export all symbols:
# symbols = [_pad, _eos] + list(_characters) #+ _arpabet
symbols = [_pad, _eos, _sep] + _initials + _finals
