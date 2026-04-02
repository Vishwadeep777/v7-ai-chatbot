# 🤖 V-7 AI Chatbot

A high-performance, full-stack AI chatbot built with **FastAPI** and ****. This project demonstrates real-time asynchronous streaming, secure API integration, and custom persona-based prompting.

## 🚀 Live Demo
Check out the live application: [v7-ai-chatbot.onrender.com](https://v7-ai-chatbot.onrender.com)

---

## 🛠️ Tech Stack

* **Backend:** FastAPI (Python 3.11)
* **AI Engine:**  Llama 3.3 via Groq Flash API
* **Frontend:** HTML5, CSS3 (Modern UI), JavaScript (ES6+)
* **Deployment:** Render
* **Key Libraries:** ` Llama 3.3 via Groq`, `uvicorn`, `marked.js` (Markdown), `highlight.js` (Code Highlighting)

---

## ✨ Key Features

* **Real-time Streaming:** Implements server-side events (SSE) for word-by-word response delivery.
* **Dynamic Personas:** Toggle between specialized AI experts (Java Senior Dev, Resume Coach, Creative Mode) using System Instructions.
* **Responsive UI:** Mobile-friendly design inspired by modern chat interfaces.
* **Code Sandbox:** Built-in syntax highlighting and "One-Click Copy" for code snippets.
* **Rate Limiting:** Custom middleware to prevent API abuse based on client IP.

---

## 🏗️ Engineering Challenges Solved

### 1. Versioning & Compatibility
Resolved `404 NOT_FOUND` errors by migrating from legacy `v1beta` endpoints to the stable **Gemini 2.0 Flash** model using the ` Llama 3.3 via Groq` SDK.

### 2. Cloud Deployment & Port Binding
Optimized deployment on **Render** by resolving "Port Scan Timeout" issues. Implemented explicit port binding to `10000` to ensure 100% uptime on cloud instances.

### 3. Asynchronous Handling
Utilized Python's `asyncio` and FastAPI's `StreamingResponse` to handle non-blocking AI completions, ensuring the UI remains responsive during long generations.

---

## 📸 Screenshots

| Desktop View | Mobile View |
| :--- | :--- |
| ![Desktop UI](https://via.placeholder.com/400x200?text=V-7+AI+Desktop) | ![Mobile UI](https://via.placeholder.com/200x400?text=V-7+AI+Mobile) |

---

## ⚙️ Local Setup

1.  **Clone the Repo:**
    ```bash
    git clone [https://github.com/Vishvdeep777/v7-ai-chatbot.git](https://github.com/Vishvdeep777/v7-ai-chatbot.git)
    cd v7-ai-chatbot
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Environment Variables:**
    Create a `.env` file or export your key:
    ```bash
    export GROQ_API_KEY='your_api_key_here'
    ```

4.  **Run the Server:**
    ```bash
    uvicorn main:app --reload
    ```

---

## 👤 Author

**Vishvdeep ** * GitHub: [@Vishvdeep777](https://github.com/Vishvdeep777)  
* Education: B.E. in Information Technology, SGBAU (2025)

---

> *Disclaimer: This project was built for educational purposes to explore LLM integration and cloud architecture.*
