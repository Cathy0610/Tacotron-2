import sys
sys.path.append('/home/zhousp/Tacotron-2')
from tacotron.utils import pinyin

def convert(origin):
    newseq = []
    head = 0
    i = head
    while i < len(origin):
        token = origin[i]
        if token.isdigit(): # prosodic struct
            if head != i:
                # print(''.join(origin[head:i]))
                newseq += list(pinyin.split_pinyin(''.join(origin[head:i])))
                # print(str(list(pinyin.split_pinyin(''.join(origin[head:i])))))
            if token == '1':
                newseq.append('`')
            elif token == '2':
                newseq.append('/')
            elif token == '3':
                newseq.append(',')
            elif token == '4':
                newseq.append('.')
        elif token == '.':  # sep between char inside single prosodic word
            if head != i:
                # print(''.join(origin[head:i]))
                newseq += list(pinyin.split_pinyin(''.join(origin[head:i])))
                # print(str(list(pinyin.split_pinyin(''.join(origin[head:i])))))
            newseq.append('-')
        else:
            if not token.islower(): # abort parsing English phoneme
                return None
            i = i+1
            continue
        i = i + 1
        head = i
    return newseq

if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        lines = [line.strip().split('|') for line in f.readlines()]
    
    newlines = []
    for line in lines:
        newtokenseq = convert(line[-1].split())
        if newtokenseq is not None:
            line[-1] = ' '.join([nt for nt in newtokenseq if len(nt)])
            newlines.append(line)
    
    with open(sys.argv[2], 'w') as f:
        f.write('\n'.join(['|'.join(line) for line in newlines]))