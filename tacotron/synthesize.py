import argparse
import os
import re
import time
from time import sleep

import tensorflow as tf
from hparams import hparams, hparams_debug_string
from infolog import log
from tacotron.synthesizer import Synthesizer
from tqdm import tqdm
import json

import numpy as np
import test_style_alignments


def generate_fast(model, text):
	model.synthesize([text], None, None, None, None)


def run_live(args, checkpoint_path, hparams):
	#Log to Terminal without keeping any records in files
	log(hparams_debug_string())
	synth = Synthesizer()
	synth.load(checkpoint_path, hparams)

	#Generate fast greeting message
	greetings = 'Hello, Welcome to the Live testing tool. Please type a message and I will try to read it!'
	log(greetings)
	generate_fast(synth, greetings)

	#Interaction loop
	while True:
		try:
			text = input()
			generate_fast(synth, text)

		except KeyboardInterrupt:
			leave = 'Thank you for testing our features. see you soon.'
			log(leave)
			generate_fast(synth, leave)
			sleep(2)
			break

def run_eval(args, checkpoint_path, output_dir, hparams, sentences):
	if hparams.tacotron_style_transfer:
		if hparams.tacotron_style_reference_audio is None:
			_sentences = []
			for s in sentences:
				_sentences += [s] * len(test_style_alignments.test_alignments)
			test_alignments = test_style_alignments.test_alignments * len(sentences)
			sentences = _sentences
			
			ref_audios = None
		else:
			ref_audios = hparams.tacotron_style_reference_audio
			test_alignments = None
	else:
		ref_audios = None
		test_alignments = None
		

	eval_dir = os.path.join(output_dir, 'eval')
	log_dir = os.path.join(output_dir, 'logs-eval')

	if args.model == 'Tacotron-2':
		assert os.path.normpath(eval_dir) == os.path.normpath(args.mels_dir)

	#Create output path if it doesn't exist
	os.makedirs(eval_dir, exist_ok=True)
	os.makedirs(log_dir, exist_ok=True)
	os.makedirs(os.path.join(log_dir, 'wavs'), exist_ok=True)
	os.makedirs(os.path.join(log_dir, 'plots'), exist_ok=True)

	log(hparams_debug_string())
	synth = Synthesizer()
	synth.load(checkpoint_path, hparams)

	#Set inputs batch wise
	sentences = [sentences[i: i+hparams.tacotron_synthesis_batch_size] for i in range(0, len(sentences), hparams.tacotron_synthesis_batch_size)]
	test_alignments = [test_alignments[i: i+hparams.tacotron_synthesis_batch_size] for i in range(0, len(test_alignments), hparams.tacotron_synthesis_batch_size)] if test_alignments is not None else test_alignments
	ref_audios = [ref_audios[i: i+hparams.tacotron_synthesis_batch_size] for i in range(0, len(ref_audios), hparams.tacotron_synthesis_batch_size)] if ref_audios is not None else ref_audios

	log('Starting Synthesis')
	with open(os.path.join(eval_dir, 'map.txt'), 'w') as file:
		if ref_audios is not None:
			for i, texts in enumerate(tqdm(sentences)):
				start = time.time()

				basenames = ['batch_{}_sentence_{}'.format(i, j) for j in range(len(texts))]
				
				mel_filenames, speaker_ids = synth.synthesize(texts, basenames, eval_dir, log_dir, mel_filenames=ref_audios[i], gst_only=(args.gst_only == 'True'))

				for elems in zip(texts, mel_filenames, speaker_ids):
					file.write('|'.join([str(x) for x in elems]) + '\n')
		elif test_alignments is None:
			for i, texts in enumerate(tqdm(sentences)):
				start = time.time()

				basenames = ['batch_{}_sentence_{}'.format(i, j) for j in range(len(texts))]
				
				mel_filenames, speaker_ids = synth.synthesize(texts, basenames, eval_dir, log_dir, None, gst_only=(args.gst_only == 'True'))

				for elems in zip(texts, mel_filenames, speaker_ids):
					file.write('|'.join([str(x) for x in elems]) + '\n')
		else:
			for i, texts in enumerate(tqdm(sentences)):
				start = time.time()

				basenames = []
				for j, text in enumerate(texts):
					idx = i * hparams.tacotron_synthesis_batch_size + j
					s_id = int(idx / len(test_style_alignments.test_alignments))
					w_id = int(idx % len(test_style_alignments.test_alignments))
					basenames.append('weight_{}_sentence_{}'.format(w_id, s_id))
				
				mel_filenames, speaker_ids = synth.synthesize(texts, basenames, eval_dir, log_dir, None, test_alignments=test_alignments[i], gst_only=(args.gst_only == 'True'))

				for elems in zip(texts, mel_filenames, test_alignments[i], speaker_ids):
					file.write('|'.join([str(x) for x in elems]) + '\n')

	log('synthesized mel spectrograms at {}'.format(eval_dir))
	return eval_dir

def run_synthesis(args, checkpoint_path, output_dir, hparams):
	GTA = (args.GTA == 'True')
	if GTA:
		synth_dir = os.path.join(output_dir, 'gta')

		#Create output path if it doesn't exist
		os.makedirs(synth_dir, exist_ok=True)
	else:
		synth_dir = os.path.join(output_dir, 'natural')

		#Create output path if it doesn't exist
		os.makedirs(synth_dir, exist_ok=True)


	log(hparams_debug_string())
	synth = Synthesizer()
	synth.load(checkpoint_path, hparams, gta=GTA)

	metadata_filename = os.path.join(args.input_dir, 'train14k_py.txt')
	with open(metadata_filename, encoding='utf-8') as f:
		metadata = [line.strip().split('|') for line in f]
		frame_shift_ms = hparams.hop_size / hparams.sample_rate
		hours = sum([int(x[4]) for x in metadata]) * frame_shift_ms / (3600)
		log('Loaded metadata for {} examples ({:.2f} hours)'.format(len(metadata), hours))

	#Set inputs batch wise
	metadata = [metadata[i: i+hparams.tacotron_synthesis_batch_size] for i in range(0, len(metadata), hparams.tacotron_synthesis_batch_size)]

	log('Starting Synthesis')
	if hparams.lpc_util:
		mel_dir = os.path.join(args.input_dir, hparams.lpc_taco_train_target_dir)
	else:
		mel_dir = os.path.join(args.input_dir, 'mels')
	# wav_dir = os.path.join(args.input_dir, 'audio')
	with open(os.path.join(synth_dir, 'map.txt'), 'w') as file:
		for i, meta in enumerate(tqdm(metadata)):
			texts = [m[-1] for m in meta]
			if hparams.lpc_util:
				basenames = [m[1][4:-4] for m in meta]
				mel_filenames = [os.path.join(mel_dir, m[1][4:]) for m in meta]
			else:
				mel_filenames = [os.path.join(mel_dir, m[1]) for m in meta]
				basenames = [os.path.basename(m).replace('.npy', '').replace('mel-', '') for m in mel_filenames]
			# wav_filenames = [os.path.join(wav_dir, m[0]) for m in meta]
			mel_output_filenames, speaker_ids = synth.synthesize(texts, basenames, synth_dir, None, mel_filenames, gst_only=(args.gst_only == 'True'))

			# for elems in zip(wav_filenames, mel_filenames, mel_output_filenames, speaker_ids, texts):
			for elems in zip(mel_filenames, mel_output_filenames, speaker_ids, texts):
				file.write('|'.join([str(x) for x in elems]) + '\n')
	log('synthesized mel spectrograms at {}'.format(synth_dir))
	return os.path.join(synth_dir, 'map.txt')

def tacotron_synthesize(args, hparams, checkpoint, sentences=None):
	output_dir = 'tacotron_' + args.output_dir

	checkpoint_path = checkpoint
	try:
		# checkpoint_path = tf.train.get_checkpoint_state(checkpoint).model_checkpoint_path
		log('loaded model at {}'.format(checkpoint_path))
	except:
		raise RuntimeError('Failed to load checkpoint at {}'.format(checkpoint))

	if hparams.tacotron_synthesis_batch_size < hparams.tacotron_num_gpus:
		raise ValueError('Defined synthesis batch size {} is smaller than minimum required {} (num_gpus)! Please verify your synthesis batch size choice.'.format(
			hparams.tacotron_synthesis_batch_size, hparams.tacotron_num_gpus))

	if hparams.tacotron_synthesis_batch_size % hparams.tacotron_num_gpus != 0:
		raise ValueError('Defined synthesis batch size {} is not a multiple of {} (num_gpus)! Please verify your synthesis batch size choice!'.format(
			hparams.tacotron_synthesis_batch_size, hparams.tacotron_num_gpus))

	if args.mode == 'eval':
		return run_eval(args, checkpoint_path, output_dir, hparams, sentences)
	elif args.mode == 'synthesis':
		return run_synthesis(args, checkpoint_path, output_dir, hparams)
	else:
		run_live(args, checkpoint_path, hparams)
