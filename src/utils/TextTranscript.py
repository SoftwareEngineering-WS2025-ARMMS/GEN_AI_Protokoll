import copy
import json


class TextTranscript:
    _transcript = []

    @property
    def transcript(self):
        return copy.deepcopy(self._transcript)

    def transcript_as_dict(self) -> dict:
        return {
            "segments": [
                {"speaker": speaker, "text": text} for speaker, text in self._transcript
            ]
        }

    @transcript.setter
    def transcript(self, new_transcript: list[tuple[str, str]] | str | dict):
        self._transcript = []
        if isinstance(new_transcript, list):
            last_speaker = None
            for (speaker, text) in new_transcript:
                if speaker == last_speaker:
                    self._transcript[-1] = (last_speaker, self._transcript[-1][1] + '. ' + text)
                else:
                    self._transcript.append((speaker, text))
                last_speaker = speaker
            return

        if type(new_transcript) is str:
            new_transcript = json.loads(new_transcript)

        assert (
            len(new_transcript) == 1 and "segments" in new_transcript.keys()
        ), "Wrong JSON format"

        assert all(
            [
                isinstance(segment, dict) and len(segment) == 2
                for segment in new_transcript["segments"]
            ]
        ), "Wrong JSON format"
        last_speaker = None
        for segment in new_transcript["segments"]:
            if segment["speaker"] == last_speaker:
                self._transcript[-1] = (last_speaker, self._transcript[-1][1] + '. ' + segment["text"])
            else:
                self._transcript.append((segment["speaker"], segment["text"]))
            last_speaker = segment["speaker"]

    def __init__(self, transcript: list[tuple[str, str]] | str | dict):
        """
        Initializes a transcript object as a list of (speaker, text) tuples.
        """
        self.transcript = transcript
