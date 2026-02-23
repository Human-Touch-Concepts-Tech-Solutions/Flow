# Package imports



from fastapi import FastAPI
import os
import requests

app = FastAPI()

AI_URL = os.getenv("AI_URL")

@app.get("/")
def health():
    return {"status": "backend running"}

@app.get("/ai-test")
def ai_test():
    response = requests.post(
        f"{AI_URL}/api/generate",
        json={
            "model": "mistral",
            "prompt": "Say hello",
            "stream": False
        }
    )
    return response.json()