from src.utils import TextTranscript

dialog = [
    ("Alice", "Hey, did you finish the report for the meeting tomorrow?"),
    ("Bob", "Not yet. I’m still working on the data analysis."),
    ("Alice", "Do you need any help? I could take a look at the charts."),
    ("Bob", "That would be great. The trends in Q3 are a bit confusing."),
    ("Alice", "Sure thing. Let me grab my laptop, and we’ll sort it out."),
    ("Bob", "Thanks, Alice. I appreciate it."),
    ("Alice", "No problem. Teamwork makes the dream work!")
]

dict_dialog = {"segments": [
    {"speaker": "Alice", "text": "Hey, did you finish the report for the meeting tomorrow?"},
    {"speaker": "Bob", "text": "Not yet. I’m still working on the data analysis."},
    {"speaker": "Alice", "text": "Do you need any help? I could take a look at the charts."},
    {"speaker": "Bob", "text": "That would be great. The trends in Q3 are a bit confusing."},
    {"speaker": "Alice", "text": "Sure thing. Let me grab my laptop, and we’ll sort it out."},
    {"speaker": "Bob", "text": "Thanks, Alice. I appreciate it."},
    {"speaker": "Alice", "text": "No problem. Teamwork makes the dream work!"}
]}


def test_transcript_getters():
    t = TextTranscript(dialog)
    assert t.transcript == dialog
    assert t.transcript_as_dict() == dict_dialog


def test_transcript_setters():
    t = TextTranscript([])
    assert t.transcript == []
    assert t.transcript_as_dict() == {"segments": []}
    t.transcript = dialog
    assert t.transcript == dialog
    assert t.transcript_as_dict() == dict_dialog
    t.transcript = []
    assert t.transcript == []
    assert t.transcript_as_dict() == {"segments": []}
    t.transcript = dict_dialog
    assert t.transcript == dialog
    assert t.transcript_as_dict() == dict_dialog