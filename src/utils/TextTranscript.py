import json
import copy

class TextTranscript:
    _transcript = []

    @property
    def transcript(self):
        return copy.deepcopy(self._transcript)

    def transcript_as_dict(self) -> dict:
        return {"segments": [{"speaker": speaker, "text": text} for speaker, text in self._transcript]}

    @transcript.setter
    def transcript(self, new_transcript: list[tuple[str, str]] | str | dict):
        if isinstance(new_transcript, list):
            self._transcript = new_transcript
            return

        if type(new_transcript) is str:
            new_transcript = json.loads(new_transcript)
        assert len(new_transcript) == 1 and "segments" in new_transcript.keys(), "Wrong JSON format"
        assert all([isinstance(segment, dict) and len(segment) == 2 for segment in new_transcript["segments"]]), "Wrong JSON format"
        self._transcript = [(segment["speaker"], segment["text"]) for segment in new_transcript["segments"]]


    def __init__(self, transcript: list[tuple[str, str]] | str | dict):
        """
        Initializes a transcript object as a list of (speaker, text) tuples.
        """
        self.transcript = transcript


