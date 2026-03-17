from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import FileResponse
import os
import requests
import json
import httpx
import time

app = FastAPI()

# ================= RATE LIMITER =================
# This dictionary remembers IP addresses and the times they sent messages
RATE_LIMIT_STORE = {}
MAX_REQUESTS_PER_MINUTE = 5

def check_rate_limit(request: Request):
    client_ip = request.client.host
    current_time = time.time()

    # If this is a new IP, create a list for them
    if client_ip not in RATE_LIMIT_STORE:
        RATE_LIMIT_STORE[client_ip] = []

    # Clean up old requests (remove timestamps older than 60 seconds)
    RATE_LIMIT_STORE[client_ip] = [t for t in RATE_LIMIT_STORE[client_ip] if current_time - t < 60]

    # If they have 5 or more requests in the last 60 seconds, block them!
    if len(RATE_LIMIT_STORE[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a minute before sending another message.")

    # Otherwise, record this new request time
    RATE_LIMIT_STORE[client_ip].append(current_time)


# ================= ROUTES =================
@app.get("/")
def read_root():
    return FileResponse("index.html")

# Notice we added 'request: Request' and 'Depends(check_rate_limit)' here!
@app.post("/chat", dependencies=[Depends(check_rate_limit)])
def chat(data: dict, request: Request):
    try:
        user_message = data.get("message", "")

        if not user_message.strip():
            raise HTTPException(status_code=400, detail="Empty message")

        api_token = os.environ.get("REPLICATE_API_TOKEN")

        # ===== LOCAL OLLAMA =====
        if not api_token:
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3",
                        "prompt": user_message
                    },
                    timeout=60
                )

                full_response = ""

                for line in response.text.split('\n'):
                    if line.strip():
                        try:
                            data_obj = json.loads(line)
                            if 'response' in data_obj:
                                full_response += data_obj['response']
                        except:
                            pass

                return {"response": full_response}

            except:
                return {"response": "❌ Ollama not running. Start with: ollama serve"}

        # ===== REPLICATE =====
        else:
            try:
                with httpx.Client(timeout=60) as client:
                    res = client.post(
                        "https://api.replicate.com/v1/predictions",
                        headers={"Authorization": f"Token {api_token}"},
                        json={
                            "version": "e5582ad7d6418d0df7bb5ab665f46d7c23b39553f46a937e4189b531175ef652",
                            "input": {"prompt": user_message}
                        }
                    )

                    pred_id = res.json().get("id")

                    for _ in range(60):
                        result = client.get(
                            f"https://api.replicate.com/v1/predictions/{pred_id}",
                            headers={"Authorization": f"Token {api_token}"}
                        ).json()

                        if result["status"] == "succeeded":
                            output = result.get("output", [])
                            return {"response": "".join(output)}

                        time.sleep(1)

                return {"response": "Timeout error"}

            except Exception as e:
                return {"response": str(e)}

    except HTTPException as he:
        # If the rate limiter blocks them, send that exact error to the frontend
        return {"response": he.detail}
    except Exception as e:
        return {"response": str(e)}