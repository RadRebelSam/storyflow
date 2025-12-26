# 🎙️ StoryFlow

> **Decode the DNA of Great Conversations.**
> StoryFlow uses AI to dissect long-form podcasts and videos, revealing the hidden narrative architecture, interview techniques, and mental models used by world-class creators.

![License](https://img.shields.io/badge/license-MIT-blue) ![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB) ![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688) ![Python](https://img.shields.io/badge/python-3.10%2B-blue)

## ✨ Features

*   **🎬 Narrative Arc Visualization**: See the structure of a conversation at a glance (The Setup, The Conflict, The Release).
*   **💡 "Learning Moments" Extraction**: Automatically identifies and extracts actionable frameworks, mental models, and key insights.
*   **🗣️ Speaker Diarization**: Distinguishes between Host and Guest (via Deepgram) to analyze interviewing techniques vs. storytelling.
*   **⚡ Dual-Mode Transcription**: 
    *   **Free**: Robust YouTube Captions extraction (via `yt-dlp`).
    *   **Pro (Deepgram)**: High-fidelity audio transcription with Speaker Labels (Diarization).
    *   **Pro (Whisper)**: Support for **OpenAI Whisper** and **Grok Whisper** (beta) for high accuracy. 
    *   **Unlimited Length**: Smart chunking handles large files (>25MB) automatically.
*   **🎙️ Podcast Browser**: Browse episodes directly from any RSS feed URL and analyze them instanly.
*   **🧠 Local Caching**: Never pay to analyze the same video twice. Results are cached locally via SQLite.
*   **🔌 Multi-LLM Support**: Plug in your favorite AI—OpenAI, Anthropic, or Gemini.

## 🛠️ Tech Stack

*   **Frontend**: React, Vite, Vanilla CSS.
*   **Backend**: Python, FastAPI, SQLite.
*   **Intelligence**: `yt-dlp` (Media Extraction), `deepgram-sdk` (Diarization), OpenAI/Anthropic/Grok (Analysis & Transcription).

---

## 🚀 Getting Started

Follow these steps to run StoryFlow on your local machine.

### Prerequisites

1.  **Python 3.10+**
2.  **Node.js 18+**
3.  **FFmpeg** (Required for Audio Processing)
    *   **Manual Install Required** (if `winget` fails):
        *   Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z).
        *   Extract to `C:\ffmpeg`.
        *   **Crucial**: Add `C:\ffmpeg\bin` to your System PATH manually.
        *   Verify by running `ffmpeg -version` in a NEW terminal.
    *   *Note: FFmpeg is required for Deepgram, Whisper (chunking), and generic Audio URL support.*

### 1. Backend Setup

Open a terminal in the `backend` directory:

```bash
cd backend
```

**Install Dependencies:**
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install packages
# Install minimal packages (optimized list)
pip install -r requirements.txt
```

**Run Server:**
```bash
uvicorn main:app --reload
```
The backend will start at `http://localhost:8000`.

### 2. Frontend Setup

Open a **new** terminal in the `frontend` directory:

```bash
cd frontend
```

**Install & Run:**
```bash
npm install
npm run dev
```
The frontend will start at `http://localhost:5173`.

---

## 📖 Usage Guide

1.  **Open the App**: Go to **http://localhost:5173**.
2.  **Configure AI**:
    *   Click the **Gear Icon** (Settings).
    *   Select your Provider (e.g., OpenAI) and enter your API Key.
    *   Select your Provider (e.g., OpenAI) and enter your API Key.
    *   **Transcription**: Choose between YouTube (Free), Deepgram, OpenAI Whisper, or Grok Whisper.
    *   Enter the corresponding API Key for proper functionality.
3.  **Analyze Content**:
    *   Paste a YouTube URL (e.g., a podcast interview).
    *   **OR** Click **Podcast Browser** to find an episode from an RSS feed.
    *   Click **Analyze**.
    *   Watch as StoryFlow generates the "Narrative Arc" and extracts insights in real-time.

---

## 🎓 Acknowledgments

This project was developed using the knowledge from **The AI Architect** curriculum at **[Superlinear Academy](https://www.superlinear.academy/c/aa/)**, founded by **[Yuzheng Sun](https://www.lizheng.ai/)**.

---

## 📄 License

**MIT License**

Copyright (c) 2025 StoryFlow

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
