import json

from backend.utils import *
from backend.utils.FunctionTool import FunctionTool


class ProtocolHandler:

    def __init__(self, protocol_id: int = 0):
        self.protocol_id = protocol_id
        self._recording = None
        self._annotation = None
        self._transcript = None
        self._protocol = None

    @property
    def transcript(self):
        return self._transcript

    def generate_transcript(self, audio_file) -> TextTranscript:
        self._recording = Recording.from_file(audio_file)
        self._annotation = Annotation()
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

    @staticmethod
    def _create_protocol(title: str, numberOfAttendees: int, agendaItems: list, date: str = "", place: str = ""):
        """
        Create a protocol object for the given parameters.
        :param title: The title of the protocol
        :param date: The date of the protocol in YYYY-MM-DD format
        :param place: The place of the protocol
        :param numberOfAttendees: The number of speakers in the protocol
        :param agendaItems: The agenda items of the protocol as an array of JSON objects.
        Each object has two string properties: 'title' and 'explanation',
        where title is the title of the item and explanation is the explanation of the item.
        :return: a protocol object.
        """
        return None

    def generate_protocol(self, form: dict | None = None, language: str = 'DE') -> dict:
        assert self._transcript is not None, "Cannot generate a protocol without any generated transcript"
        """
        if form is None:
            form = {
                         "parameters": {
                            "type": "object",
                             "properties": {
                                 "title": {"type": "string", "description": "The title of the protocol"},
                                 "date": {"type": "string",
                                          "description": "The date of the protocol in YYYY-MM-DD format"},
                                 "place": {"type": "string", "description": "The place of the protocol"},
                                 "numberOfAttendees": {"type": "integer",
                                                       "description": "The number of speakers in the protocol"},
                                 "agendaItems": {"type": "array",
                                                 "description": "The agenda items of the protocol as an array of JSON objects. "
                                                                "Each objects has two string properties: 'title' and 'explanation', "
                                                                "where title is the title of the item and explanation is the "
                                                                "explanation of the item."}
                             },
                             "required": ["title", "numberOfAttendees", "agendaItems"]
                         }
                     }
        """
        tool = FunctionTool(ProtocolHandler._create_protocol, metadata=form)
        print(tool.metadata)
        return {}
        client = OpenAIClient.new_client()
        system_message = ("You will receive from the user a transcript in the following JSON format as message:\n\n"
                          "{'segment': [{'speaker': 'speaker1', 'text': 'text1'}, {'speaker': 'speaker2', 'text': 'text2'}, ...]}\n\n"
                          "which corresponds to the dialog of a recorded meeting. You create a protocol object from that dialog."
                          f" The title, place and agenda items must be in the language '{language}'.")
        user_message = json.dumps(self._transcript.transcript_as_dict())
        output = client.prompt(system_message, user_message, tools=[tool])
        get_tool = [t for t in output["tools"] if t["tool"] == tool][0]
        return get_tool