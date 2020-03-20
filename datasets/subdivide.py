import argparse
import random

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--num', type=int, default=1000, help='number of utterances for each emotion category')
	parser.add_argument('--label', type=float, default=0.3, help='proportion of labeled utterances for each emotion category')
	parser.add_argument('--origin', help='original train.txt file path')
	parser.add_argument('--to', help='path to save new train.txt file')
	args = parser.parse_args()

	label_rate = max(0, min(1, args.label))
	print('[Using label rate %d]' % label_rate)
	with open(args.origin, 'r') as f:
		raw_lines = [line.strip() for line in f.readlines()]
		entries = [line.split('|') for line in raw_lines]
	print('extracted %d utterances from %s' % (len(raw_lines), args.origin))

	emo_dict = {}
	for entry in entries:
		if entry[5] in emo_dict:
			emo_dict[entry[5]].append(entry)
		else:
			emo_dict[entry[5]] = [entry]
	
	labeled = []
	unlabeled = []
	for k, v in emo_dict.items():
		num = min(len(v), args.num)
		label_num = int(num * label_rate)
		unlabel_num = num - label_num
		v_sample = random.sample(v, num)
		labeled += v_sample[:label_num]
		unlabeled += v_sample[label_num:]
		print('>\'%s\': \t%d\t utterances' % (k, len(v)))
		print('[# Samples:\t %d \t]' % args.num)
		print('[# Labeled:\t %d \t]' % label_num)
		print('[# Unlabeled:\t %d \t]' % unlabel_num)
	
	for entry in unlabeled:
		entry[5] = 'NONE'
	result = labeled + unlabeled
	random.shuffle(result)
	print('>>Total num: \t%d\t utterances' % len(result))

	with open(args.to, 'w') as f:
		text = '\n'.join(['|'.join(entry) for entry in result])
		f.write(text)
	print('Written to %s' % args.to)
	