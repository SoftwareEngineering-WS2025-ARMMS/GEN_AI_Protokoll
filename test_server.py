import asyncio
import json

import websockets
import sys
import wave

async def run_test(uri):
    async with websockets.connect(uri) as websocket:

        wf = wave.open(sys.argv[1], "rb")
        await websocket.send('{ "config" : { "sample_rate" : %d } }' % (wf.getframerate()))
        buffer_size = int(wf.getframerate() * 0.2) # 0.2 seconds of audio
        while True:
            data = wf.readframes(buffer_size)

            if len(data) == 0:
                break

            await websocket.send(data)
            await websocket.recv()

        await websocket.send('{"eof" : 1}')
        result = await websocket.recv()
        print("Final result:", json.loads(result).get("text"))

asyncio.run(run_test('ws://localhost:2700'))