import os
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import numpy as np
from datasets import audio
from wavenet_vocoder.util import is_mulaw, is_mulaw_quantize, mulaw, mulaw_quantize
from tacotron.utils.symbols import _sep, _final_er, phonesplit

def build_from_path(hparams, input_dirs, mel_dir, linear_dir, wav_dir, n_jobs=12, tqdm=lambda x: x):
	"""
	Preprocesses the speech dataset from a gven input path to given output directories

	Args:
		- hparams: hyper parameters
		- input_dir: input directory that contains the files to prerocess
		- mel_dir: output directory of the preprocessed speech mel-spectrogram dataset
		- linear_dir: output directory of the preprocessed speech linear-spectrogram dataset
		- wav_dir: output directory of the preprocessed speech audio dataset
		- n_jobs: Optional, number of worker process to parallelize across
		- tqdm: Optional, provides a nice progress bar

	Returns:
		- A list of tuple describing the train examples. this should be written to train.txt
	"""

	# We use ProcessPoolExecutor to parallelize across processes, this is just for
	# optimization purposes and it can be omited
	executor = ProcessPoolExecutor(max_workers=n_jobs)
	futures = []
	index = 1
	for input_dir in input_dirs:
		with open(os.path.join(input_dir, 'metadata.csv'), encoding='utf-8') as f:
			for line in f:
				parts = line.strip().split('|')
				basename = parts[0]
				wav_path = os.path.join(input_dir, 'wavs', '{}.wav'.format(basename))
				text = parts[2]
				futures.append(executor.submit(partial(_process_utterance, mel_dir, linear_dir, wav_dir, basename, wav_path, text, hparams)))
				index += 1

	return [future.result() for future in tqdm(futures) if future.result() is not None]


def build_from_path_databaker(hparams, input_dirs, mel_dir, linear_dir, wav_dir, n_jobs=12, tqdm=lambda x: x):
	"""
	Preprocesses https://www.data-baker.com/open_source.html dataset from a gven input path to given output directories

	Args:
		- hparams: hyper parameters
		- input_dir: input directory that contains the files to prerocess
		- mel_dir: output directory of the preprocessed speech mel-spectrogram dataset
		- linear_dir: output directory of the preprocessed speech linear-spectrogram dataset
		- wav_dir: output directory of the preprocessed speech audio dataset
		- n_jobs: Optional, number of worker process to parallelize across
		- tqdm: Optional, provides a nice progress bar

	Returns:
		- A list of tuple describing the train examples. this should be written to train.txt
	"""

	# We use ProcessPoolExecutor to parallelize across processes, this is just for
	# optimization purposes and it can be omited
	executor = ProcessPoolExecutor(max_workers=n_jobs)
	futures = []
	for in_dir, label in input_dirs:
		with open(os.path.join(in_dir, 'metadata.txt'), 'r', encoding='utf-8') as f:
			lines = f.readlines()
			# print(len(lines))
			for lineidx in range(0, len(lines), 2):
			# for lineidx in [14050]:
				wavidx_raw, text_raw = lines[lineidx].split()
				phonemes_raw = lines[lineidx+1].strip().split()
				wav_path = os.path.join(in_dir, ('wav/%s.wav' % wavidx_raw))

				text_clean = text_raw
				for punctuation in ['“', '”', '、', '，', '。', '：', '；', '？', '！', '—', '——', '…', '……', '#']:
					text_clean = text_clean.replace(punctuation, '')
				
				print(wav_path)
				symbols = []
				while len(text_clean):
					if text_clean[0].isdigit():
						symbols += text_clean[0]
						text_clean = text_clean[1:]
					else:
						if text_clean[0]<='z' and text_clean[0]>='A': # English segment
							# 1. insert sep between word
							if len(symbols) and not symbols[-1].isdigit():
								symbols.append(_sep)
							# 2. extract word
							while text_clean[0]<='z' and text_clean[0]>='A':
								text_clean = text_clean[1:]
							# 3. remove leading '/' sep (if any)
							if phonemes_raw[0] is '/':
								phonemes_raw = phonemes_raw[1:]
							# 4. extract phoneme
							while len(phonemes_raw)>0 and phonemes_raw[0] != '/':
								symbols.append(phonemes_raw[0])
								phonemes_raw = phonemes_raw[1:]
							# 5. remove tail '/'
							phonemes_raw = phonemes_raw[1:]
						elif text_clean[0]!='儿' or (len(symbols)==0) or (symbols[-1][:-1] not in _final_er): # Chinese segment
							if len(symbols) and not symbols[-1].isdigit():
								symbols.append(_sep)
							symbols += phonesplit(phonemes_raw[0])
							phonemes_raw = phonemes_raw[1:]
							text_clean = text_clean[1:]
						else:	# 儿化音
							text_clean = text_clean[1:]
				text = ' '.join(symbols)
				# print(text)
				
				futures.append(executor.submit(partial(_process_utterance, mel_dir, linear_dir, wav_dir, wavidx_raw, wav_path, text, label, hparams)))

	return [future.result() for future in tqdm(futures) if future.result() is not None]



def build_from_path_databaker_os(hparams, input_dirs, mel_dir, linear_dir, wav_dir, n_jobs=12, tqdm=lambda x: x):
	"""
	Preprocesses https://www.data-baker.com/open_source.html dataset from a gven input path to given output directories

	Args:
		- hparams: hyper parameters
		- input_dir: input directory that contains the files to prerocess
		- mel_dir: output directory of the preprocessed speech mel-spectrogram dataset
		- linear_dir: output directory of the preprocessed speech linear-spectrogram dataset
		- wav_dir: output directory of the preprocessed speech audio dataset
		- n_jobs: Optional, number of worker process to parallelize across
		- tqdm: Optional, provides a nice progress bar

	Returns:
		- A list of tuple describing the train examples. this should be written to train.txt
	"""

	# We use ProcessPoolExecutor to parallelize across processes, this is just for
	# optimization purposes and it can be omited
	executor = ProcessPoolExecutor(max_workers=n_jobs)
	futures = []
	in_dir = input_dirs[0]
	with open(os.path.join(in_dir, 'ProsodyLabeling/000001-010000.txt'), 'r', encoding='utf-8') as f:
		content = f.readlines()
		num = int(len(content)//2)
		for lineidx in range(num):
			wavidx_raw = content[lineidx*2].split()[0]
			wav_path = os.path.join(in_dir, ('Wave/%s.wav' % wavidx_raw))
			text = content[lineidx*2+1].strip()
			futures.append(executor.submit(partial(_process_utterance, mel_dir, linear_dir, wav_dir, wavidx_raw, wav_path, text, hparams)))

	return [future.result() for future in tqdm(futures) if future.result() is not None]



def _process_utterance(mel_dir, linear_dir, wav_dir, index, wav_path, text, emo_label, hparams):
	"""
	Preprocesses a single utterance wav/text pair

	this writes the mel scale spectogram to disk and return a tuple to write
	to the train.txt file

	Args:
		- mel_dir: the directory to write the mel spectograms into
		- linear_dir: the directory to write the linear spectrograms into
		- wav_dir: the directory to write the preprocessed wav into
		- index: the numeric index to use in the spectogram filename
		- wav_path: path to the audio file containing the speech input
		- text: text spoken in the input audio file
		- emo_label: emotion label of the input audio
			- 'N': neutral
			- 'A': angry
			- 'D': disgust
			- 'F': fearful
			- 'H': happy
			- 'S': sad
			- 'U': surprised
		- hparams: hyper parameters

	Returns:
		- A tuple: (audio_filename, mel_filename, linear_filename, time_steps, mel_frames, linear_frames, text)
	"""
	try:
		# Load the audio as numpy array
		wav = audio.load_wav(wav_path, sr=hparams.sample_rate)
	except FileNotFoundError: #catch missing wav exception
		print('file {} present in csv metadata is not present in wav folder. skipping!'.format(
			wav_path))
		return None

	#Trim lead/trail silences
	if hparams.trim_silence:
		wav = audio.trim_silence(wav, hparams)

	#Pre-emphasize
	preem_wav = audio.preemphasis(wav, hparams.preemphasis, hparams.preemphasize)

	#rescale wav
	if hparams.rescale:
		wav = wav / np.abs(wav).max() * hparams.rescaling_max
		preem_wav = preem_wav / np.abs(preem_wav).max() * hparams.rescaling_max

		#Assert all audio is in [-1, 1]
		if (wav > 1.).any() or (wav < -1.).any():
			raise RuntimeError('wav has invalid value: {}'.format(wav_path))
		if (preem_wav > 1.).any() or (preem_wav < -1.).any():
			raise RuntimeError('wav has invalid value: {}'.format(wav_path))

	#Mu-law quantize
	if is_mulaw_quantize(hparams.input_type):
		#[0, quantize_channels)
		out = mulaw_quantize(wav, hparams.quantize_channels)

		#Trim silences
		start, end = audio.start_and_end_indices(out, hparams.silence_threshold)
		wav = wav[start: end]
		preem_wav = preem_wav[start: end]
		out = out[start: end]

		constant_values = mulaw_quantize(0, hparams.quantize_channels)
		out_dtype = np.int16

	elif is_mulaw(hparams.input_type):
		#[-1, 1]
		out = mulaw(wav, hparams.quantize_channels)
		constant_values = mulaw(0., hparams.quantize_channels)
		out_dtype = np.float32

	else:
		#[-1, 1]
		out = wav
		constant_values = 0.
		out_dtype = np.float32

	# Compute the mel scale spectrogram from the wav
	mel_spectrogram = audio.melspectrogram(preem_wav, hparams).astype(np.float32)
	mel_frames = mel_spectrogram.shape[1]

	if mel_frames > hparams.max_mel_frames and hparams.clip_mels_length:
		return None

	if hparams.predict_linear:
		#Compute the linear scale spectrogram from the wav
		linear_spectrogram = audio.linearspectrogram(preem_wav, hparams).astype(np.float32)
		linear_frames = linear_spectrogram.shape[1]

		#sanity check
		assert linear_frames == mel_frames

	if hparams.use_lws:
		#Ensure time resolution adjustement between audio and mel-spectrogram
		fft_size = hparams.n_fft if hparams.win_size is None else hparams.win_size
		l, r = audio.pad_lr(wav, fft_size, audio.get_hop_size(hparams))

		#Zero pad audio signal
		out = np.pad(out, (l, r), mode='constant', constant_values=constant_values)
	else:
		#Ensure time resolution adjustement between audio and mel-spectrogram
		l_pad, r_pad = audio.librosa_pad_lr(wav, hparams.n_fft, audio.get_hop_size(hparams), hparams.wavenet_pad_sides)

		#Reflect pad audio signal on the right (Just like it's done in Librosa to avoid frame inconsistency)
		out = np.pad(out, (l_pad, r_pad), mode='constant', constant_values=constant_values)

	assert len(out) >= mel_frames * audio.get_hop_size(hparams)

	#time resolution adjustement
	#ensure length of raw audio is multiple of hop size so that we can use
	#transposed convolution to upsample
	out = out[:mel_frames * audio.get_hop_size(hparams)]
	assert len(out) % audio.get_hop_size(hparams) == 0
	time_steps = len(out)

	# Write the spectrogram and audio to disk
	audio_filename = 'audio-{}.npy'.format(index)
	mel_filename = 'mel-{}.npy'.format(index)
	np.save(os.path.join(wav_dir, audio_filename), out.astype(out_dtype), allow_pickle=False)
	np.save(os.path.join(mel_dir, mel_filename), mel_spectrogram.T, allow_pickle=False)

	linear_filename = ''
	if hparams.predict_linear:
		linear_filename = 'linear-{}.npy'.format(index)
		np.save(os.path.join(linear_dir, linear_filename), linear_spectrogram.T, allow_pickle=False)

	# Return a tuple describing this training example
	return (audio_filename, mel_filename, linear_filename, time_steps, mel_frames, emo_label, text)
