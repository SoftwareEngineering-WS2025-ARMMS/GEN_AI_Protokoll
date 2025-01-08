import json
import os
import secrets
import requests
from jose import jwt

from flask import Flask, jsonify, request
from flask_oidc import OpenIDConnect
from flask_cors import CORS

from src.rest.ProtocolHandler import ProtocolHandler
from src.utils.DataBaseConnection import DataBaseConnection

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

rest_dir = os.path.dirname(__file__)

app.config.update({
    "SECRET_KEY": secrets.token_hex(32),
    "OIDC_CLIENT_SECRETS": os.path.join(rest_dir, "../../.venv/client_secrets.json"),
    "OIDC_SCOPES": ["openid", "organization", "email"],
    "OIDC_INTROSPECTION_AUTH_METHOD": "client_secret_post",
    "DEBUG": True,
})

oidc = OpenIDConnect(app)

protocols : dict[tuple[str, str], ProtocolHandler] = {}

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
    except Exception as e:
        return {"error": str(e)}


@app.route("/api/upload-audio", methods=["POST"])
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
            transcript = protocol.generate_transcript(audio_file=file)
            cropped = transcript.transcript_as_dict()
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
            protocols[(protocol.id, subject)] = protocol
            return jsonify({"id": protocol.id, "persons": result}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file type"}), 400


@app.route("/api/annotate", methods=["POST", "PUT"])
def edit_speakers():
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    subject = validate_token(token)['sub']
    try:
        speaker_map = request.json
        protocol_id = request.args["id"]
        try:
            protocol = protocols[(protocol_id, subject)]
        except KeyError:
            return jsonify({"error": "The speakers you are trying to save do not exist."}), 404
        protocol.edit_speakers(speaker_map)
        return jsonify(protocol.transcript.transcript_as_dict()), 200
    except AssertionError:
        return jsonify({"error": "The speakers' names do not match!"}), 404
    except KeyError as e:
        return jsonify({"error": f"Wrong request format. Error: {str(e)}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/transcript", methods=["POST"])
def get_proto_draft_text():
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    subject = validate_token(token)['sub']
    try:
        protocol_id = request.args["id"]
        try:
            protocol = protocols[(protocol_id, subject)]
        except KeyError:
            return jsonify({"error": "The protocol you are trying to edit does not exist."}), 404
        try:
            protocol.transcript.transcript = request.json
        except Exception as e:
            print(e)
        return jsonify(protocol.generate_protocol()), 200
    except AssertionError as e:
        return (
            jsonify({"error": f"Could not generate protocol due to:\n{str(e)}!"}),
            400,
        )
    except KeyError as e:
        return jsonify({"error": f"Wrong request format. Error: {str(e)}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/protocol", methods=["POST"])
def save_protocol():
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    decoded_token = validate_token(token)
    subject = decoded_token['sub']
    try:
        organizations = decoded_token['organization_info']
        assert len(organizations.keys()) == 1
        name = list(organizations.keys())[0]
        organization_id = organizations[name]['id']
        protocol_id = request.args.get("id")
        try:
            protocol = protocols[(protocol_id, subject)]
        except KeyError:
            return jsonify({"error": "The protocol you are trying to save does not exist."}), 404
        protocol.protocol = request.json
        database.save_protocol(protocol.protocol, organization=organization_id)
        protocols.pop((protocol_id, subject))
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/protocol", methods=["GET"])
def get_protocol():
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    decoded_token = validate_token(token)
    try:
        organizations = decoded_token['organization_info']
        assert len(organizations.keys()) == 1
        name = list(organizations.keys())[0]
        organization_id = organizations[name]['id']
        protocol_id = int(request.args["id"])
        return jsonify(database.get_protocol_by_id(protocol_id, organization_id)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/protocol", methods=["DELETE"])
def delete_protocol():
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    decoded_token = validate_token(token)
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


@app.route("/api/protocols", methods=["GET"])
def get_protocols():
    token = request.headers['Authorization'].split(None, 1)[1].strip()
    decoded_token = validate_token(token)
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
