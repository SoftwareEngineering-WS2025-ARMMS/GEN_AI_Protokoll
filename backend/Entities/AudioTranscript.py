from backend.Entities.TextTranscript import TextTranscript
from backend.Entities.Recording import Recording

class AudioTranscript:
    _transcript = []

    def __init__(self, transcript: list[tuple[str, Recording]]):
        """
           Initializes a transcript object as a list of (speaker, recording) tuples.
        """
        self._transcript = transcript

    def to_transcript(self) -> TextTranscript:
        """
        Transforms the audio transcript to a text transcript.
        :return:
        """
        return None