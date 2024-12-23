import json

from flask import Flask, request, jsonify

from backend.rest.ProtocolHandler import ProtocolHandler
from backend.utils.DataBaseConnection import DataBaseConnection

app = Flask(__name__)

protocol = ProtocolHandler()

db_metadata = json.load(open('../../.venv/database_metadata.json', 'r'))

database = DataBaseConnection(**db_metadata)

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
        return jsonify({'error': str(e)}), 500

@app.route('/api/protocol', methods=['POST'])
def save_protocol():
    try:
        user_id = request.args.get('user_id')
        database.save_protocol(protocol.generate_protocol(), user_id=user_id)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/protocol', methods=['GET'])
def get_protocol():
    try:
        protocol_id = int(request.args.get('id'))
        user_id = request.args.get('user_id')
        return jsonify(database.get_protocol_by_id(protocol_id, user_id)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/protocols', methods=['GET'])
def get_protocols():
    try:
        user_id = request.args.get('user_id')
        return jsonify(database.get_protocol_summaries(user_id)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)