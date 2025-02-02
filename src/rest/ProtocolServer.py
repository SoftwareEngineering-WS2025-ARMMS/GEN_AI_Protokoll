import json
import os
import requests
from jose import jwt
import threading
import traceback

from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from werkzeug.datastructures import FileStorage

from src.rest.ProtocolHandler import ProtocolHandler, secrets
from src.utils.DataBaseConnection import DataBaseConnection

app = Flask(__name__)
CORS(app)

rest_dir = os.path.dirname(__file__)


app.config.update({
    "SECRET_KEY": secrets.token_hex(32),
    "OIDC_CLIENT_SECRETS": os.path.join(rest_dir, "../../.venv/client_secrets.json"),
    "OIDC_SCOPES": ["openid", "organization", "email"],
    "OIDC_INTROSPECTION_AUTH_METHOD": "client_secret_post"
})

protocol_pool : dict[tuple[str, str], tuple[ProtocolHandler, threading.Lock]] = {}
protocol_pool_lock = threading.Lock()

db_metadata = json.load(open(os.path.join(rest_dir, "../../.venv/database_metadata.json"), "r"))

database = DataBaseConnection(**db_metadata)


def validate_token(token):
    jwks_url = "https://keycloak-armms.rayenmanai.site/realms/ARMMS-Platform/protocol/openid-connect/certs"
    response = requests.get(jwks_url)
    response.raise_for_status()
    jwks = response.json()
    try:
        decoded_token = jwt.decode(
            token,
            jwks,
            audience="ProtoGen-Authorization",
            issuer="https://keycloak-armms.rayenmanai.site/realms/ARMMS-Platform"
        )
        return decoded_token
    except Exception:
        return {"error": traceback.format_exc()}


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin")
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@app.route("/api/speakers", methods=["GET"])
@cross_origin(origins=[
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://protogen-armms.rayenmanai.site"
], supports_credentials=True)
def generate_speaker_text():
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    subject = validate_token(token)['sub']
    protocol_id = request.args["id"]
    try:
        protocol, _ = protocol_pool[(protocol_id, subject)]
    except KeyError:
        return jsonify({"error": "The speakers you are trying to save do not exist."}), 404
    if not protocol.transcript_generation_done:
        percentage = protocol.transcript_generation_percentage
        ann_done = protocol.annotation_done
        transcript_done = protocol.transcript_generation_done
        return jsonify({"percentage": percentage * 100.,
                        "isAnnotationDone": ann_done,
                        "isDone": transcript_done,
                        "persons": []})

    if protocol.transcript_generation_percentage < - 1e-3:
        protocol_pool_lock.acquire()
        protocol_pool.pop((protocol_id, subject))
        protocol_pool_lock.release()
        return jsonify({"error": "Unable to read the audio."}), 401
    cropped = protocol.transcript.transcript_as_dict()
    for segment in cropped["segments"]:
        segment["text"] = (
            segment["text"][: max(100, len(segment["text"]))] + "..."
        )
    result = {}
    for speaker in set(map(lambda s: s["speaker"], cropped["segments"])):
        result[speaker] = " ".join(
            map(
                lambda s: s["text"],
                filter(
                    lambda s: s["speaker"] == speaker,
                    cropped["segments"],
                ),
            )
        )
    return jsonify({"percentage": 100.,
                    "isAnnotationDone": True,
                    "isDone": True,
                    "persons": result}), 200


def safe_transcript_generation(protocol: ProtocolHandler, file: FileStorage, lock: threading.Lock):
    lock.acquire()
    ProtocolHandler.generate_transcript(protocol, file)
    lock.release()


@app.route("/api/upload-audio", methods=["POST"])
@cross_origin(origins=[
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://protogen-armms.rayenmanai.site"
], supports_credentials=True)
def upload_recording():
    if "file" not in request.files:
        return jsonify({"error": "No file was received by the server"}), 400
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    subject = validate_token(token)['sub']
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    if file:
        try:
            protocol = ProtocolHandler()
            protocol_pool_lock.acquire()
            lock = threading.Lock()
            protocol_pool[(protocol.id, subject)] = protocol, lock
            protocol_pool_lock.release()
            thread = threading.Thread(target=safe_transcript_generation, args=(protocol, file, lock))
            thread.start()
            return jsonify({"id": protocol.id}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file type"}), 400


@cross_origin(origins=[
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://protogen-armms.rayenmanai.site"
], supports_credentials=True)
@app.route("/api/annotate", methods=["POST", "PUT"])
def edit_speakers():
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    subject = validate_token(token)['sub']
    try:
        speaker_map = request.json
        protocol_id = request.args["id"]
        try:
            protocol, lock = protocol_pool[(protocol_id, subject)]
        except KeyError:
            return jsonify({"error": "The speakers you are trying to save do not exist."}), 404
        lock.acquire()
        protocol.edit_speakers(speaker_map)
        transcript = protocol.transcript.transcript_as_dict()
        lock.release()
        return jsonify(transcript), 200
    except AssertionError:
        return jsonify({"error": "The speakers' names do not match!"}), 404
    except KeyError as e:
        return jsonify({"error": f"Wrong request format. Error: {str(e)}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@cross_origin(origins=[
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://protogen-armms.rayenmanai.site"
], supports_credentials=True)
@app.route("/api/transcript", methods=["POST"])
def get_proto_draft_text():
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    subject = validate_token(token)['sub']
    try:
        protocol_id = request.args["id"]
        try:
            protocol, lock = protocol_pool[(protocol_id, subject)]
        except KeyError:
            return jsonify({"error": "The protocol you are trying to edit does not exist."}), 404
        lock.acquire()
        try:
            protocol.transcript.transcript = request.json
        except Exception as e:
            print(e)
        protocol_draft = protocol.generate_protocol()
        lock.release()
        return jsonify(protocol_draft), 200
    except AssertionError as e:
        return (
            jsonify({"error": f"Could not generate protocol due to:\n{str(e)}!"}),
            400,
        )
    except KeyError as e:
        return jsonify({"error": f"Wrong request format. Error: {str(e)}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@cross_origin(origins=[
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://protogen-armms.rayenmanai.site"
], supports_credentials=True)
@app.route("/api/protocol", methods=["POST"])
def save_protocol():
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    decoded_token: dict[str, any] = validate_token(token)
    subject = decoded_token['sub']
    try:
        organizations = decoded_token['organization_info']
        assert len(organizations.keys()) == 1
        name = list(organizations.keys())[0]
        organization_id = organizations[name]['id']
        protocol_id = request.args.get("id")
        try:
            protocol, lock = protocol_pool[(protocol_id, subject)]
        except KeyError:
            return jsonify({"error": "The protocol you are trying to save does not exist."}), 404
        lock.acquire()
        protocol.protocol = request.json
        lock.release()
        database.save_protocol(protocol.protocol, organization=organization_id)
        protocol_pool_lock.acquire()
        protocol_pool.pop((protocol_id, subject))
        protocol_pool_lock.release()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@cross_origin(origins=[
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://protogen-armms.rayenmanai.site"
], supports_credentials=True)
@app.route("/api/protocol", methods=["GET"])
def get_protocol():
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    decoded_token: dict[str, any] = validate_token(token)
    try:
        organizations = decoded_token['organization_info']
        assert len(organizations.keys()) == 1
        name = list(organizations.keys())[0]
        organization_id = organizations[name]['id']
        protocol_id = int(request.args["id"])
        return jsonify(database.get_protocol_by_id(protocol_id, organization_id)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@cross_origin(origins=[
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://protogen-armms.rayenmanai.site"
], supports_credentials=True)
@app.route("/api/protocol", methods=["DELETE"])
def delete_protocol():
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    decoded_token: dict[str, any] = validate_token(token)
    try:
        organizations = decoded_token['organization_info']
        assert len(organizations.keys()) == 1
        name = list(organizations.keys())[0]
        organization_id = organizations[name]['id']
        protocol_id = int(request.args.get("id"))
        database.remove_protocol(protocol_id, organization_id)
        return jsonify({'response': 'Successfully removed the protocol'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@cross_origin(origins=[
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "https://protogen-armms.rayenmanai.site"
], supports_credentials=True)
@app.route("/api/protocols", methods=["GET"])
def get_protocols():
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    decoded_token: dict[str, any] = validate_token(token)
    try:
        organizations = decoded_token['organization_info']
        assert len(organizations.keys()) == 1
        name = list(organizations.keys())[0]
        organization_id = organizations[name]['id']
        print(database.get_protocol_summaries(organization_id))
        return jsonify(database.get_protocol_summaries(organization_id)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
