import asyncio
import json

import websockets

from src.utils.Recording import Recording
from src.utils.TextTranscript import TextTranscript

VOSK_SERVER_URL = "ws://localhost:2700"


class AudioTranscript:
    _transcript = []

    def __init__(self, transcript: list[tuple[str, Recording]]):
        """
        Initializes a transcript object as a list
         of (speaker, recording) tuples.
        """
        self._transcript = transcript

    def to_transcript(self) -> TextTranscript:
        """
        Transforms the audio transcript to a text transcript.
        :return:
        """
        return TextTranscript(asyncio.run(self.process_with_vosk()))

    async def process_with_vosk(self) -> list[tuple[str, str]]:
        results = []
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
                results.append((speaker, json.loads(result).get("text")))
        return results
