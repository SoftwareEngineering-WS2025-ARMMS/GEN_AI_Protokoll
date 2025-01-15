import pytest

from src.utils import Annotation


def test_pyannote_key_exists():
    Annotation()


@pytest.mark.parametrize("n, expected", [(1, []), (2, []), (3, [])])
def test_annotate(n: int, expected: list[tuple[str, float, float]]):
    pass