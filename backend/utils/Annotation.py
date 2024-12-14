from pyannote.audio import Pipeline
import torch

from backend.utils.Recording import Recording

class Annotation:

    @staticmethod
    def __import_key__() -> str:
        with open('.venv/PYANNOTE_KEY', 'r') as file:
            return file.readline()

    __key__ = __import_key__()

    def __init__(self, device='cpu'):
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=Annotation.__key__)
        self.pipeline.to(torch.device(device))

    def annotate(self, recording: Recording) -> list[tuple[str, float, float]]:
        diarization = self.pipeline(recording.waveform)
        l = diarization.itertracks(yield_label=True)
        return [(speaker, turn.start, turn.end) for (turn, _, speaker) in l]