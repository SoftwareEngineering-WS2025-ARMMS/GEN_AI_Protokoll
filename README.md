# GEN_AI_Protokoll

To run the server, some packages need to be installed (Recommended to use python venv or conda).

## Pyannote
### 1. install pyannote.audio
```bash
pip install pyannote.audio
```
### 2. HuggingFace
1. Sign up / log in into [HuggingFace](https://huggingface.co/).
2. Accept [pyannote/segmentation-3.0 user conditions](https://huggingface.co/pyannote/segmentation-3.0)
3. Accept [pyannote/speaker-diarization-3.1 user conditions](https://hf.co/pyannote/speaker-diarization-3.1)
4. Create access token at [HuggingFace](https://hf.co/settings/tokens).
5. Copy the access token to a safe place so that it is not open to the public. (If using venv, we recommend to copy it to a file '.venv/PYANNOTE_KEY')

PS: If you chose another file location, don't forget to change the "\_\_key_path\_\_" in "utils/Annotation.py" to your file path.

## OpenAI key
As we use for the moment the OpenAI API, it is required that you have an access token stored in a safe place (If using venv, we recommend to copy it to a file '.venv/CHATGPT_API')
PS: If you chose another file location, don't forget to change the "\_\_key_path\_\_" in "utils/OpenAIClient.py" to your file path.


# Running the server
To run the server, run the file 'backend/rest/ProtocolServer.py'