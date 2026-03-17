from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import FileResponse, StreamingResponse
import os
import requests
import json
import time
import replicate

app = FastAPI()

# ================= RATE LIMITER =================
# remembers IP addresses and the times they sent messages
RATE_LIMIT_STORE = {}
MAX_REQUESTS_PER_MINUTE = 5

def check_rate_limit(request: Request):
    client_ip = request.client.host
    current_time = time.time()

    if client_ip not in RATE_LIMIT_STORE:
        RATE_LIMIT_STORE[client_ip] = []

    # Clean up old requests (older than 60 seconds)
    RATE_LIMIT_STORE[client_ip] = [t for t in RATE_LIMIT_STORE[client_ip] if current_time - t < 60]

    if len(RATE_LIMIT_STORE[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=429, 
            detail="Too many requests. Please wait a minute before sending another message."
        )

    RATE_LIMIT_STORE[client_ip].append(current_time)


# ================= ROUTES =================

@app.get("/")
def read_root():
    return FileResponse("index.html")


@app.post("/chat", dependencies=[Depends(check_rate_limit)])
async def chat(data: dict, request: Request):
    user_message = data.get("message", "").strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Empty message")

    api_token = os.environ.get("REPLICATE_API_TOKEN")

    # ===== CASE 1: REPLICATE STREAMING (ONLINE) =====
    if api_token:
        def stream_replicate():
            try:
                # Using the official SDK for real-time word-by-word delivery
                for event in replicate.stream(
                    "meta/meta-llama-3-8b-instruct",
                    input={
                        "prompt": user_message,
                        "prompt_template": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou are V-7 AI, a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
                    }
                ):
                    yield str(event)
            except Exception as e:
                yield f"Error connecting to Replicate: {str(e)}"

        return StreamingResponse(stream_replicate(), media_type="text/plain")

    # ===== CASE 2: LOCAL OLLAMA (OFFLINE FALLBACK) =====
    else:
        try:
            # Note: Streaming with requests/ollama locally is done differently, 
            # so for this fallback we return the full string at once.
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3",
                    "prompt": user_message,
                    "stream": False
                },
                timeout=60
            )
            
            data_obj = response.json()
            full_text = data_obj.get("response", "No response from local AI.")
            
            # We wrap this in a generator so the frontend can still use its "while" loop
            def stream_local():
                yield full_text
                
            return StreamingResponse(stream_local(), media_type="text/plain")

        except Exception as e:
            def stream_error():
                yield "❌ Ollama not running and no API Token found. Run: `ollama serve`"
            return StreamingResponse(stream_error(), media_type="text/plain")
