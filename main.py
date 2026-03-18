import os
import time
import requests
import json
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

app = FastAPI()

# ================= RATE LIMITER =================
RATE_LIMIT_STORE = {}
MAX_REQUESTS_PER_MINUTE = 10 

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
    persona = data.get("persona", "general") 

    if not user_message:
        raise HTTPException(status_code=400, detail="Empty message")

    # Define Persona Instructions
    instructions = {
        "general": "You are V-7 AI, a helpful assistant created by Vishvdeep Pundge.",
        "java_expert": "You are V-7 AI, a Senior Java Developer. Provide clean, efficient code using Java 21+ features.",
        "resume_expert": "You are V-7 AI, an IT Career Coach. Help the user optimize their resume for ATS.",
        "creative": "You are V-7 AI, a creative storyteller. Provide imaginative and expressive responses."
    }
    
    selected_instruction = instructions.get(persona, instructions["general"])
    
    # Notice we are now pulling the GROQ_API_KEY from Render!
    api_key = os.environ.get("GROQ_API_KEY")

    # ===== CASE 1: GROQ API STREAMING (ONLINE) =====
    if api_key:
        async def stream_groq():
            try:
                # We are using Meta's flagship Llama 3.3 70B model via Groq!
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": selected_instruction},
                            {"role": "user", "content": user_message}
                        ],
                        "stream": True
                    },
                    stream=True,
                    timeout=30
                )
                
                if response.status_code == 429:
                    yield "⚠️ V-7 AI is cooling down (Groq Rate Limit). Please wait a moment."
                    return
                elif response.status_code == 401:
                    yield "❌ Groq API Error: Invalid API Key. Please check your Render Environment Variables."
                    return
                elif response.status_code != 200:
                    yield f"❌ Groq API Error: {response.text}"
                    return
                    
                # Parse the Server-Sent Events (SSE) stream from Groq
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            data_str = decoded_line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data_json = json.loads(data_str)
                                chunk = data_json["choices"][0]["delta"].get("content", "")
                                if chunk:
                                    yield chunk
                            except Exception:
                                pass
            except Exception as e:
                yield f"❌ Connection Error: {str(e)}"

        return StreamingResponse(stream_groq(), media_type="text/plain")

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
                yield "❌ Error: GROQ_API_KEY not found in Render Environment Variables."
            return StreamingResponse(stream_error(), media_type="text/plain")
