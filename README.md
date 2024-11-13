# GEN_AI_Protokoll

```docker compose up -d```

check that ollama is running: 

```http://localhost:7869/```
should display "Ollama is running"

Pull llama model 3:

```curl -X POST http://localhost:7869/api/pull -d '{"model": "llama3"}'```

Example to test llama api from command line:

```curl -X POST http://localhost:7869/api/generate -d "{\"model\": \"llama3\",  \"prompt\":\"explain mitosis briefly\", \"stream\": false}"```

to test the simple webui that has a connector to upload an audio file:

```python3 test_backend.py```
and then open ```index.html``` in the browser