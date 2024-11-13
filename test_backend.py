from flask import Flask, request, jsonify
from flask_cors import CORS
import wave
import json
import os
import websockets
import asyncio
import httpx

app = Flask(__name__)
CORS(app)

VOSK_SERVER_URL = "ws://localhost:2700"
LLAMA_SERVER_URL = "http://localhost:7869/api/generate"

@app.route('/process-audio', methods=['POST'])
def process_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    audio_file_path = os.path.join("/tmp", file.filename)
    file.save(audio_file_path)

    # Ensure audio meets Vosk requirements
    try:
        with wave.open(audio_file_path, "rb") as wf:
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                return jsonify({"error": "Audio file must be mono PCM WAV format with a 16kHz sample rate."}), 400

            # Run Vosk processing asynchronously
            transcript = asyncio.run(process_with_vosk(audio_file_path))
            if transcript:
                summary = asyncio.run(get_llama_summary(transcript))
                return jsonify({"transcript": transcript, "summary": summary}), 200
            else:
                return jsonify({"error": "Transcription failed"}), 500
    finally:
        os.remove(audio_file_path)


async def process_with_vosk(audio_file_path):
    async with websockets.connect(VOSK_SERVER_URL) as websocket:
        with wave.open(audio_file_path, "rb") as wf:
            await websocket.send('{ "config" : { "sample_rate" : %d } }' % (wf.getframerate()))
            buffer_size = int(wf.getframerate() * 0.2)  # 0.2 seconds of audio
            while True:
                data = wf.readframes(buffer_size)

                if len(data) == 0:
                    break

                await websocket.send(data)
                await websocket.recv()

            await websocket.send('{"eof" : 1}')
            result = await websocket.recv()
            print("Final result:", json.loads(result).get("text"))
            return json.loads(result).get("text", "")

async def get_llama_summary(transcript):
    prompt = f"Fasse folgendes zusammen und erkläre es auf deutsch: {transcript}"

    # Prepare data for the request
    data = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }

    # Send request to LLaMA API
    async with httpx.AsyncClient() as client:
        response = await client.post(LLAMA_SERVER_URL, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            print(result.get("response"))
            return result.get("response", "")
        else:
            print(f"Error from LLaMA API: {response.status_code}, {response.text}")
            return "Error: LLaMA failed to generate a summary."


if __name__ == '__main__':
    app.run(port=8000)
