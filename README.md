# 🔍 Lyze — Intelligence Canvas

> Ask questions across your PDFs, images, audio, and video — powered by local AI.

![TypeScript](https://img.shields.io/badge/TypeScript-94%25-blue)
![Python](https://img.shields.io/badge/Python-FastAPI-green)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## How it works

Lyze has two parts:

- **Frontend** — React/TypeScript web app (the UI you see)
- **Backend** — Python FastAPI server that runs locally on your machine, handling file ingestion, AI processing, and vector search

Your files never leave your machine. The backend runs at `http://localhost:8000`.

---

## Quick Start

### Prerequisites
- [Node.js](https://nodejs.org) (for the frontend)
- [Python 3.10+](https://python.org) (for the backend)
- [Ollama](https://ollama.com) (for free local AI — recommended)

### 1. Clone the repo
```bash
git clone https://github.com/arjunpil/lyze-multimodal-rag.git
cd lyze-multimodal-rag
```

### 2. Set up the backend

**Windows:**
```
start_backend.bat
```

**Mac / Linux:**
```bash
chmod +x start_backend.sh
./start_backend.sh
```

This installs Python dependencies and starts the backend at `http://localhost:8000`.

### 3. Pull AI models (first time only)
```bash
ollama pull mistral
ollama pull llava
ollama pull nomic-embed-text
```

### 4. Start the frontend
```bash
npm install
npm run dev
```

Open **http://localhost:3000** — Lyze is ready.

---

## Supported file types

| Type | Formats |
|---|---|
| Documents | PDF |
| Images | JPG, PNG, WEBP, BMP, TIFF |
| Audio | MP3, WAV, M4A, FLAC, OGG |
| Video | MP4, MOV, AVI, MKV |

---

## Configuration

Edit `backend/.env` to change AI providers:

```env
# Free local (default)
LLM_PROVIDER=ollama
LLM_MODEL=mistral
VISION_PROVIDER=ollama
VISION_MODEL=llava
EMBED_PROVIDER=ollama
EMBED_MODEL=nomic-embed-text

# Or use cloud providers
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

Restart the backend after changing `.env`.

---

## License
MIT
