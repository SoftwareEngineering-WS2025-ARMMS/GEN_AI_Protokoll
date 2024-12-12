import os
from io import BytesIO
import torchaudio

from pydub import AudioSegment

class Recording:

    _extension: str
    _content: AudioSegment

    _supported_extensions = ['.wav']

    @property
    def extension(self) -> str:
        return self._extension

    @property
    def content(self) -> AudioSegment:
        return self._content

    @property
    def waveform(self):
        waveform, sample_rate = self._waveform
        return {"waveform": waveform, "sample_rate": sample_rate}

    @extension.setter
    def extension(self, extension: str) -> None:
        if extension not in self._supported_extensions:
            raise ValueError(f'Extension {extension} not supported for the moment')
        self._extension = extension

    @content.setter
    def content(self, content: AudioSegment) -> None:
        self._content = content

    def __init__(self, extension: str, content: AudioSegment, waveform: tuple[any, int]):
        self.extension = extension
        self.content = content
        self._waveform = waveform

    @classmethod
    def from_file_path(cls, file_path: str) -> "Recording":
        extension = os.path.splitext(file_path)[-1]
        content = AudioSegment.from_file(file_path)
        recording = cls(extension=extension, content=content, waveform=torchaudio.load(file_path))
        return recording

    @classmethod
    def from_file(cls, file, extension='.wav') -> "Recording":
        byte_obj = BytesIO(file.read())
        content = AudioSegment.from_file(byte_obj, format=extension[1:])
        recording = cls(extension=extension, content=content, waveform=torchaudio.load(byte_obj))
        return recording

    def trim_recording(self, annotation: list[tuple[str, float, float]]) -> list[tuple[str, "Recording"]]:
        waveform, sample_rate = self._waveform

        # Ensure waveform is 2D for consistency (shape: [channels, samples])
        if waveform.ndim == 1:
            waveform = waveform.unsqueeze(0)

        split_segments = []
        for speaker, start, end in annotation:
            # Extract segment using PyTorch slicing
            start_idx = int(start * sample_rate)
            end_idx = int(end * sample_rate)
            segment = waveform[:, start_idx:end_idx]
            segment_waveform = segment, sample_rate

            #Extract segment form AudioSegment
            start_idx = int(start * 1000)
            end_idx = int(end * 1000)
            segment_audio = self.content[start_idx:end_idx]

            recording = Recording(extension=self.extension, content=segment_audio, waveform=segment_waveform)
            split_segments.append((speaker, recording))
        return split_segments
