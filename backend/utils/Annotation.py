from pyannote.audio import Pipeline
import torch

from backend.utils.Recording import Recording

class Annotation:

    __key_path__ = '.venv/PYANNOTE_KEY'

    def __init__(self, device='cpu'):
        with open(Annotation.__key_path__, 'r') as file:
            key = file.readline()
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=key)
        self.pipeline.to(torch.device(device))

    def annotate(self, recording: Recording) -> list[tuple[str, float, float]]:
        diarization = self.pipeline(recording.waveform)
        l = diarization.itertracks(yield_label=True)
        return [(speaker, turn.start, turn.end) for (turn, _, speaker) in l]