# Prepare the MultiSets dataset


The MultiSets dataset provides an easy mechanism for preparing the training data with multiple datasets.

What you need to do:
  * Put the files of all single datasets under this directory (or creat symbol links).
  * Prepare the metadata file for each single dataset.  The format of the metadata file confirms to the one for LJSpeech or DataBaker.
  * Preapre the "metadata.csv" in this directory, which serves as the index to the above datasets.  The format is explained as follows.


### Example of "metadata.csv"

  ```
  0|0|LJSpeech-1.1/metadata.csv.txt|1|LJSpeech-1.1/Wave|00_0_
  1|1|DataBaker/metadata.csv.txt|0|DataBaker/Wave|01_1_
  ```


### Format of "metadata.csv"

The "metadata.csv" stores index for each dataset.

Each line of "metadata.csv" has 6 parts separated by "|", including: 

  ```
  speaker_id|language_id|metadata_file|metadata_use_raw|wavs_dir|basename_prefix
  ```

Where
  *           "speaker_id" is the speaker_id of the dataset 
                              (特定数据集的说话人标签id, 从0开始);
  *          "language_id" is the language_id of the dataset 
                              (特定数据集的语言标签id, 从0开始);
  *        "metadata_file" is the metadata of the dataset, specifying "wav_file_name|raw text|text" 
                              (某个特定数据集的metadata文件);
  *     "metadata_use_raw" is the tag indicating if "raw text" or "text" in "metadata_file" will be used (1: raw text; 0: text) 
                              (指定使用raw text还是text作为模型输入);
  *             "wavs_dir" is the directory storing the wav files of the dataset 
                              (特定数据集的波形文件目录);
  *      "basename_prefix" specifies the basename prefix of the generated training data 
                              (通过prefix防止多个数据集的wav文件名一样, 建议格式: 两位说话人标签_语言标签_).

See [../datasets/multisets.py](../datasets/multisets.py) for more information.
