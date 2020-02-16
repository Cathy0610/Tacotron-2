_emotions = ['N', 'A', 'D', 'F', 'H', 'S', 'U']
_emotion_to_id = {s: i for i, s in enumerate(_emotions)}

def emo_to_id(label):
    return _emotion_to_id[label]