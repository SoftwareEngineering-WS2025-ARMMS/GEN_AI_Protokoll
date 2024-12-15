from flask import Flask, request, jsonify

from backend.rest.ProtocolHandler import ProtocolHandler

app = Flask(__name__)

protocol = ProtocolHandler()

@app.route('/api/upload-audio', methods=['POST'])
def upload_recording():
    if 'file' not in request.files:
        return jsonify({'error': 'No file was received by the server'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    if file:
        try:
            transcript = protocol.generate_transcript(audio_file=file)
            cropped = transcript.transcript_as_dict()
            for segment in cropped["segments"]:
                segment["text"] = segment["text"][:max(100, len(segment["text"]))] + "..."
            result = {}
            for speaker in set(map(lambda s: s["speaker"], cropped["segments"])):
                result[speaker] = " ".join(map(lambda s: s["text"] ,filter(lambda s: s["speaker"] == speaker, cropped["segments"])))
            return jsonify({'persons': result}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/annotate', methods=['POST', 'PUT'])
def edit_speakers():
    speaker_map = request.json
    try:
        protocol.edit_speakers(speaker_map)
        return jsonify(protocol.transcript.transcript_as_dict()), 200
    except AssertionError:
        return jsonify({'error': 'The speakers names do not match!'}), 500

@app.route('/api/transcript', methods=['POST'])
def get_proto_draft_text():
    try:
        return jsonify(protocol.generate_protocol()), 200
    except AssertionError as e:
        return jsonify({'error': f'Could not generate protocol due to this error: \n{str(e)}!'}), 400
    except Exception as e:
        raise e
@app.route('/saveProtokoll', methods=['POST'])
def save_protocol():
    # Not implemented yet due to barely discussed database configuration
    pass


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)