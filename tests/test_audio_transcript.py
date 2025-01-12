import os
import pytest

from src.utils import Recording, AudioTranscript

test_dir = os.path.join(os.path.dirname(__file__), 'audio_files')


@pytest.mark.parametrize('file, expected, error',
                         [(f'{test_dir}/test_de_1.wav',
                          ['aufklärung', 'ist', 'immer', 'der', 'erste', 'schritt', 'punkt'], 0),
                          (f'{test_dir}/test_de_2.wav',
                          ['und', 'das', 'war', 'denen', 'dann', 'so', 'einleuchtend', 'dass',
                           'sie', 'den', 'großvater', 'dann', 'wieder', 'zum', 'tisch', 'geholt', 'haben'], 1),
                          (f'{test_dir}/test_de_3.wav',
                          ['ich', 'muss', 'über', 'hannover', 'nach', 'hamburg', 'fahren'], 0)])
def test_to_transcript(file: str, expected: list[str], error: int) -> None:
    r = Recording.from_file_path(file)
    transcript = AudioTranscript([('A', r)])
    text = transcript.to_transcript().transcript
    assert len(text) == 1
    assert text[0][0] == 'A'
    result = text[0][1].lower().split()
    assert (abs(len(result) - len(expected)) +
            len([i for i in range(min(len(result), len(expected)))
                 if result[i] != expected[i]]) <= error)
