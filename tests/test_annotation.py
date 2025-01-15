import pytest
from os import path

from src.utils import Annotation, Recording

__test_dir__ = path.dirname(path.realpath(__file__))


def test_pyannote_key_exists():
    Annotation()


@pytest.mark.parametrize("n, expected", [(1, [('SPEAKER_00', 0.90846875, 3.94596875)]),
                                         (2, [('SPEAKER_00', 0.03096875, 5.127218750000001)]),
                                         (3, [('SPEAKER_00', 0.03096875, 2.6297187500000003)]
                                          )])
def test_annotate(n: int, expected: list[tuple[str, float, float]]):
    recording = Recording.from_file_path(f"{__test_dir__}/audio_files/test_de_{n}.wav")
    result = Annotation().annotate(recording)
    assert len(result) == len(expected)
    for i in range(len(expected)):
        r = result[i]
        e = expected[i]
        assert r[0] == e[0]
        assert abs(r[1] - e[1]) < 1e-5
        assert abs(r[2] - e[2]) < 1e-5
