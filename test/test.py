import os

d = os.path.dirname(__file__)
print(d)
os.chdir(d + '/..')

from backend.utils import *

annotation = Annotation('cuda')
recording = Recording.from_file('audio_files/test_de_1.wav')
l = annotation.annotate(recording)
recs = recording.trim_recording(l)
audio_trans = AudioTranscript(recs)
script = audio_trans.to_transcript()
[print(t) for t in script.transcript]
