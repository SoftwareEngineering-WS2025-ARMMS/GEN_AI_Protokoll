class TextTranscript:
    _transcript = []

    @property
    def transcript(self):
        return self._transcript

    @transcript.setter
    def transcript(self, new_transcript):
        self._transcript = new_transcript

    def __init__(self, transcript: list[tuple[str, str]]):
        """
        Initializes a transcript object as a list of (speaker, text) tuples.
        """
        self._transcript = transcript