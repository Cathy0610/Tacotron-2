import os

if __name__ == "__main__":
    name = 'tacoGSTsemi22k'
    token_num = 7
    test_weight = range(1, 11)

    # Extract <tacotron_style_mh_alignment> from hparams.py
    #   we are compelled to modify file hparams.py to set input alignment, since
    #   tf.contrib.training.HParams.parse ONLY support number/string/list, while our
    #   <tacotron_style_mh_alignment>.shape=(#head,1,#token)
    mh_idx = -1
    with open('hparams.py', 'r') as f:
        lines = [line.strip('\n') for line in f.readlines()]
        for idx, line in enumerate(lines):
            if line.strip().startswith('tacotron_style_mh_alignment'):
                mh_idx = idx
    if mh_idx is -1:
        raise ValueError('No <tacotron_style_mh_alignment> in hparams.py')
    # Save original <tacotron_style_mh_alignment> parameter
    origin_mh_line = lines[mh_idx]

    for token in range(token_num):
        for weight in test_weight:
            alignment = [[[(0 if j!=token else weight) for j in range(token_num)]]]
            lines[mh_idx] = "    tacotron_style_mh_alignment = %s," % str(alignment)
            with open('hparams.py', 'w') as f:
                f.write('\n'.join(lines))
            output_dir = "%s_output/token%d/weight%d" % (name, token, weight)
            cmd = "python synthesize.py --model Tacotron --tacotron_name %s --mode eval --text_list zh_sentences.txt --output_dir %s" % (name, output_dir)
            print(cmd)
            os.system(cmd)
    
    # Restore <tacotron_style_mh_alignment> parameter
    lines[mh_idx] = origin_mh_line
    with open('hparams.py', 'w') as f:
        f.write('\n'.join(lines))