import os
import time
import requests
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from google import genai
from google.genai import types

app = FastAPI()

# ================= RATE LIMITER =================
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
            detail="Too many requests. Please wait a minute."
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

    api_key = os.environ.get("GOOGLE_API_KEY")

    # ===== CASE 1: GOOGLE GEMINI STREAMING (ONLINE) =====
    if api_key:
        client = genai.Client(api_key=api_key)
        
        async def stream_gemini():
            try:
                # Using Gemini 1.5 Flash for high-speed streaming
                stream = client.models.generate_content_stream(
                    model="gemini-1.5-flash",
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction="You are V-7 AI, a helpful assistant created by Vishvdeep Pundge."
                    )
                )
                for chunk in stream:
                    if chunk.text:
                        yield chunk.text
            except Exception as e:
                yield f"❌ Gemini Error: {str(e)}"

        return StreamingResponse(stream_gemini(), media_type="text/plain")

    # ===== CASE 2: LOCAL OLLAMA (OFFLINE FALLBACK) =====
    else:
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3",
                    "prompt": user_message,
                    "stream": False
                },
                timeout=30
            )
            
            data_obj = response.json()
            full_text = data_obj.get("response", "No response from local AI.")
            
            def stream_local():
                yield full_text
                
            return StreamingResponse(stream_local(), media_type="text/plain")

        except Exception as e:
            def stream_error():
                yield "❌ Error: GOOGLE_API_KEY not found in Render settings and Ollama is not running locally."
            return StreamingResponse(stream_error(), media_type="text/plain")
