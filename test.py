from hparams import hparams
import os

if __name__ == "__main__":
    for i in range(hparams.tacotron_n_style_token):
        alignment = [(0 if j!=i else 0.8) for j in range(hparams.tacotron_n_style_token)]
        hpstr = "tacotron_style_alignment=%s" % str(alignment)
        output_dir = "tacoGST_output/token%d" % i
        cmd = "python synthesize.py --model Tacotron --tacotron_name tacoGST --mode eval --text_list zh_sentences.txt --output_dir %s --hparams=\'%s\'" % (output_dir, hpstr)
        print(hpstr, output_dir)
        print(cmd)
        os.system(cmd)