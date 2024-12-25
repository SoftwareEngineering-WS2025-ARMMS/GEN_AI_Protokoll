import base64
import hashlib
import copy
import json
import hmac
import time

from src.utils import *

class ProtocolHandler:

    __C = 0
    __SECRET_KEY__ = b'abc'

    def __init__(self, protocol_id: int = 0):
        self.protocol_id = protocol_id
        self._recording = None
        self._annotation = None
        self._transcript = None
        self._protocol = None
        t = time.time()
        hash_object = hmac.new(ProtocolHandler.__SECRET_KEY__, f'{ProtocolHandler.__C:03}'.encode(), hashlib.sha256)
        hash_digest = hash_object.digest()
        self._id = base64.urlsafe_b64encode(hash_digest).decode().rstrip("=")
        print(time.time() - t)
        ProtocolHandler.__C += 1

    @property
    def id(self):
        return self._id

    @property
    def transcript(self):
        return self._transcript

    @property
    def protocol(self):
        return copy.deepcopy(self._protocol)

    @protocol.setter
    def protocol(self, value):
        assert {'title', 'date', 'place', 'numberOfAttendees', 'agendaItems'} == set(value.keys())
        self._protocol = value

    def generate_transcript(self, audio_file) -> TextTranscript:
        self._recording = Recording.from_file(audio_file)
        self._annotation = Annotation('cuda')
        annotated_recording = self._annotation.annotate(self._recording)
        trimmed_recordings = self._recording.trim_recording(annotated_recording)
        audio_transcript = AudioTranscript(trimmed_recordings)
        self._transcript = audio_transcript.to_transcript()
        return self._transcript

    def edit_transcript(self, transcript: list[tuple[str, str]] | str | dict):
        if self._transcript is None:
            self._transcript = TextTranscript(transcript)
        self._transcript.transcript = transcript

    def edit_speakers(self, speakers: dict[str, str]):
        assert self._transcript is not None, "Cannot edit speakers without any generated transcript"
        new_transcript = [(speakers[speaker], text) for (speaker, text) in self._transcript.transcript]
        self.edit_transcript(new_transcript)

    def generate_protocol(self, form: dict | None = None, language: str = 'DE') -> dict:
        def _create_protocol(title: str, numberOfAttendees: int, agendaItems: list, date: str = "", place: str = ""):
            """
            Create a protocol object for the given parameters.
            :param title: The title of the protocol
            :param date: The date of the protocol in YYYY-MM-DD format
            :param place: The place of the protocol
            :param numberOfAttendees: The number of speakers in the protocol
            :param agendaItems: The agenda items of the protocol.
            Each item has is described by a title and a summary of its content as an explanation.
            :type agendaItems: [{"title": "str", "explanation": "str"}]
            :return: a protocol object.
            """
            return None
        if self._protocol is not None:
            return self.protocol
        assert self._transcript is not None, "Cannot generate a protocol without any generated transcript"
        tool = FunctionTool(_create_protocol, metadata=form)
        client = OpenAIClient.new_client()
        system_message = ("You will receive from the user a transcript in the following JSON format as message:\n\n"
                          "{'segment': [{'speaker': 'speaker1', 'text': 'text1'}, {'speaker': 'speaker2', 'text': 'text2'}, ...]}\n\n"
                          "which corresponds to the dialog of a recorded meeting. You create a protocol object from that dialog."
                          f" The title, place and agenda items must be in the language '{language}'.")
        user_message = json.dumps(self._transcript.transcript_as_dict())
        output = client.prompt(system_message, user_message, tools=[tool])
        get_tool = [t for t in output["tools"] if t["tool"] == tool][0]
        args = get_tool["args"]
        self._protocol = copy.deepcopy(args)
        return args


if __name__ == '__main__':
    handler = ProtocolHandler()
    print(handler.id)