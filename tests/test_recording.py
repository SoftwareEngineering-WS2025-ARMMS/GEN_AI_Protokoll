import pytest
from os import path

from src.utils import Recording

__test_dir__ = path.dirname(path.realpath(__file__))


@pytest.fixture
def test_recording():
    def is_close(a, b, epsilon=1e-8):
        return abs(a - b) < epsilon

    def intern(n: int, recording: Recording, full_length=True):
        assert n in [
            1,
            2,
            3,
        ], "There is no audio file other than 1, 2 and 3 to test."
        assert recording.extension == ".wav"
        assert recording.content.frame_width == 2
        assert recording.content.frame_rate == 16000
        assert recording.waveform["sample_rate"] == 16000
        assert recording.content.channels == 1

        if full_length:
            match n:
                case 1:
                    assert is_close(recording.content.duration_seconds, 4.096)
                case 2:
                    assert is_close(recording.content.duration_seconds, 5.104)
                case 3:
                    assert is_close(recording.content.duration_seconds, 3.456)

    return intern


@pytest.mark.parametrize("n", [1, 2, 3])
def test_from_file_path(n: int, test_recording):
    recording = Recording.from_file_path(f"{__test_dir__}/audio_files/test_de_{n}.wav")
    assert isinstance(recording, Recording)
    test_recording(n, recording)


@pytest.mark.parametrize("n", [1, 2, 3])
def test_from_file(n: int, test_recording):
    file = open(f"{__test_dir__}/audio_files/test_de_{n}.wav", "rb")
    recording = Recording.from_file(file, ".wav")
    assert isinstance(recording, Recording)
    test_recording(n, recording)


@pytest.mark.parametrize("n", [1, 2, 3])
def test_trim_recording(n: int, test_recording):
    try:
        test_from_file_path(n, test_recording)
    except AssertionError:
        assert False, (
            f"This test does not run unless "
            f"the test_from_file_path passes for n = {n}."
        )
    recording = Recording.from_file_path(f"{__test_dir__}/audio_files/test_de_{n}.wav")
    recordings = recording.trim_recording(
        annotation=[("A", 0.1, 0.5), ("B", 0.8, 1.3), ("C", 2.1, 3.4)]
    )
    for s, r in recordings:
        test_recording(n, r, full_length=False)
        match s:
            case "A":
                assert abs(r.content.duration_seconds - 0.4) < 1e-8
            case "B":
                assert abs(r.content.duration_seconds - 0.5) < 1e-8
            case "C":
                assert abs(r.content.duration_seconds - 1.3) < 1e-8
