import asyncio
import json
import os

import websockets

from src.utils.Recording import Recording
from src.utils.TextTranscript import TextTranscript

VOSK_SERVER_URL = f"ws://{os.environ.get('VOSK_HOST_URI')}:2700"


class AudioTranscript:

    def __init__(self, transcript: list[tuple[str, Recording]]):
        """
        Initializes a transcript object as a list
         of (speaker, recording) tuples.
        """
        self._transcript = transcript
        self._processed_result = []
        self._process_perc = 1.
        self._process_ended = True

    @property
    def processed_result(self):
        return self._processed_result

    @property
    def process_perc(self):
        return self._process_perc

    @property
    def process_ended(self):
        return self._process_ended

    def to_transcript(self) -> TextTranscript:
        """
        Transforms the audio transcript to a text transcript.
        :return:
        """
        return TextTranscript(asyncio.run(self.process_with_vosk()))

    async def process_with_vosk(self) -> list[tuple[str, str]]:
        self._process_ended = False
        self._process_perc = 0.
        self._processed_result = []
        length = len(self._transcript)
        it = 0
        for speaker, recording in self._transcript:
            async with websockets.connect(VOSK_SERVER_URL) as websocket:
                waveform, sample_rate = recording.waveform.values()

                # Send config message
                await websocket.send('{"config": {"sample_rate": %d}}' % sample_rate)

                # Convert waveform to 16-bit PCM format
                pcm_audio = (waveform * 32767.0).short().numpy().tobytes()

                # Send audio in chunks
                chunk_size = int(sample_rate * 0.2) * 2  # 0.2 seconds of audio
                for i in range(0, len(pcm_audio), chunk_size):
                    await websocket.send(pcm_audio[i : i + chunk_size])
                    await websocket.recv()  # Receive intermediate result

                await websocket.send('{"eof" : 1}')
                result = await websocket.recv()
                it += 1
                self._process_perc = it / length
                self._processed_result.append((speaker, json.loads(result).get("text")))
        self._process_ended = True
        self._process_perc = 1.
        return self._processed_result

    async def async_to_transcript(self) -> TextTranscript:
        """
        Transforms the audio transcript to a text transcript.
        :return:
        """
        return TextTranscript(await self.process_with_vosk())