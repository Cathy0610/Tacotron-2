# $1: taco output path
# $2: wav output path
mkdir -p $2
rm -rf $2/*
mkdir $2/outputs16
for f32file in $(ls $1)
do
    if [ "${f32file##*.}" = "f32" ]; then
        name=$(basename ${f32file} .f32)
        echo $f32file
        ~/LPCNet/test_lpcnet $1/${f32file} $2/outputs16/${name}.s16
        ffmpeg -loglevel error -f s16le -ar 16k -ac 1 -i $2/outputs16/${name}.s16 $2/${name}.wav
    fi
done
rm -rf $2/outputs16
