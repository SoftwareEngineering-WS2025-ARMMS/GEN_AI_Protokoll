import base64
import copy
import hashlib
import hmac
import json
import secrets

from src.utils import (Annotation, AudioTranscript, FunctionTool, OpenAIClient,
                       Recording, TextTranscript)


class ProtocolHandler:
    __C = 0
    __SECRET_KEY__ = bytes(secrets.token_hex(32), 'utf-8')

    def __init__(self):
        self._recording: Recording | None = None
        self._annotation: Annotation | None = None
        self._transcript: TextTranscript | None = None
        self._protocol: dict | None = None
        self._audio_transcript : AudioTranscript | None = None
        hash_object = hmac.new(
            ProtocolHandler.__SECRET_KEY__,
            f"{ProtocolHandler.__C:03}".encode(),
            hashlib.sha256,
        )
        hash_digest = hash_object.digest()
        self._id = base64.urlsafe_b64encode(hash_digest).decode().rstrip("=")
        ProtocolHandler.__C += 1

    @property
    def id(self):
        return self._id

    @property
    def transcript(self) -> TextTranscript:
        return self._transcript

    @property
    def protocol(self):
        return copy.deepcopy(self._protocol)

    @property
    def transcript_generation_done(self) -> bool:
        if self._audio_transcript is None:
            return False
        return self._audio_transcript.process_ended

    @property
    def transcript_generation_percentage(self) -> float:
        if self._audio_transcript is None:
            return 0.
        return self._audio_transcript.process_perc

    @property
    def transcript_generation_result(self) -> list[tuple[str, str]]:
        if self._audio_transcript is None:
            return []
        return self._audio_transcript.processed_result

    @property
    def annotation_done(self) -> bool:
        if self._annotation is None:
            return False
        return self._annotation.is_done

    @protocol.setter
    def protocol(self, value):
        assert {
            "title",
            "date",
            "place",
            "numberOfAttendees",
            "agendaItems",
        } == set(value.keys())
        self._protocol = value

    def __create_audio_transcript(self, audio_file) -> None:
        self._recording = Recording.from_file(audio_file)
        self._annotation = Annotation("cpu")
        annotated_recording = self._annotation.annotate(self._recording)
        trimmed_recordings = self._recording.trim_recording(annotated_recording)
        self._audio_transcript = AudioTranscript(trimmed_recordings)

    def generate_transcript(self, audio_file) -> TextTranscript:
        try:
            self.__create_audio_transcript(audio_file)
            self._transcript = self._audio_transcript.to_transcript()
            return self._transcript
        except Exception:
            pass

    def edit_transcript(self, transcript: list[tuple[str, str]] | str | dict):
        if self._transcript is None:
            self._transcript = TextTranscript(transcript)
        self._transcript.transcript = transcript

    def edit_speakers(self, speakers: dict[str, str]):
        assert (
            self._transcript is not None
        ), "Cannot edit speakers without any generated transcript"
        new_transcript = [
            (speakers[speaker], text) for (speaker, text) in self._transcript.transcript
        ]
        self.edit_transcript(new_transcript)

    def generate_protocol(self, form: dict | None = None, language: str = "DE") -> dict:
        def _create_protocol(
            title: str,
            numberOfAttendees: int,
            agendaItems: list,
            date: str = "",
            place: str = "",
        ):
            """
            Create a protocol object for the given parameters.
            :param title: The title of the protocol
            :param date: The date of the protocol in YYYY-MM-DD format
            :param place: The place of the protocol
            :param numberOfAttendees: The number of speakers in the protocol
            :param agendaItems: The agenda items of the protocol.
            Each item has is described by
                * a title
                * a summary of its content as an explanation. The explanation contains further
                details about the item, including the members who are discussing it, the
                important details mentioned and the actions to be discussed.
                An example of an agenda item for a german organization (in german)
                titel: "Anzahl der Mitglieder"
                explanation:
                "Wir durften in diesem Jahr wieder ein neues Mitglied begrüßen, welches sich
                tatkräftig und finanziell sehr engagiert. Alle Mitglieder sind weiterhin ehrenamtlich
                tätig. Alle zugeteilten Aufgaben werden vollumfänglich erfüllt.
                Sowohl die Vorstandsmitglieder, als auch die Kassenprüfung wurde wiedergewählt."
            :type agendaItems: [{"title": "str", "explanation": "str"}]
            :return: a protocol object.
            """
            return None

        assert (
            self._transcript is not None
        ), "Cannot generate a protocol without any generated transcript"
        tool = FunctionTool(_create_protocol, metadata=form)
        client = OpenAIClient.new_client()
        system_message = (
            "You will receive from the user a transcript in the following "
            "JSON format as message:\n\n"
            "{'segment': [{'speaker': 'speaker1', 'text': 'text1'}, "
            "{'speaker': 'speaker2', 'text': 'text2'}, ...]}\n\n"
            "which corresponds to the dialog of a recorded meeting."
            " You create a protocol object from that dialog."
            f" The title, place and agenda items must be "
            f"in the language '{language}'."
        )
        user_message = json.dumps(self._transcript.transcript_as_dict())
        output = client.prompt(user_prompt=user_message,
                               system_prompt=system_message, tools=[tool])
        get_tool = [t for t in output["tools"] if t["tool"] == tool][0]
        args = get_tool["args"]
        self._protocol = copy.deepcopy(args)
        return args


if __name__ == "__main__":
    handler = ProtocolHandler()
    print(handler.id)
