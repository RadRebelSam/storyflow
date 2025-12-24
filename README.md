# StoryFlow

**AI-Powered Storytelling Analysis Tool**

StoryFlow dissects long-form podcasts and videos to reveal the hidden architecture of great conversations. It helps you learn storytelling techniques, interview frameworks, and narrative structures from the best creators.

## License

MIT License

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

---

# How to Run StoryFlow Locally

## Prerequisites
1.  **Python 3.10+**
2.  **Node.js 18+**
3.  **FFmpeg** (Required for Diarization/Deepgram)
    *   Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z).
    *   Extract to `C:\ffmpeg`.
    *   Add `C:\ffmpeg\bin` to your System PATH (or the app will try to auto-detect it there).

## 1. Backend Setup (FastAPI)

Open a terminal in the `backend` folder:

```bash
cd backend
```

### Install Dependencies
```bash
# Create venv (optional but recommended)
python -m venv venv
# Windows activate
.\venv\Scripts\activate
# Mac/Linux activate
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```
*Note: This includes `fastapi`, `uvicorn`, `youtube-transcript-api`, `yt-dlp`, `deepgram-sdk`, etc.*

### Environment Variables (.env)
Create a `.env` file in the `backend` folder (optional if using the GUI Settings):
```env
# Optional defaults
SUPER_MIND_API_KEY=your_key_here
BASE_URL=https://space.ai-builders.com/backend/v1
```

### Run Server
```bash
uvicorn main:app --reload
```
The backend will start at `http://localhost:8000`.

## 2. Frontend Setup (React/Vite)

Open a **new** terminal in the `frontend` folder:

```bash
cd frontend
```

### Install Dependencies
```bash
npm install
```

### Run Server
```bash
npm run dev
```
The frontend will start at `http://localhost:5173`.

## 3. Usage & Configuration

1.  Open **http://localhost:5173** in your browser.
2.  **Configure AI**: Click the **Gear Icon** (Settings).
    *   Select your Provider (e.g., OpenAI, Anthropic, or AI Builders).
    *   Enter your API Key.
3.  **Configure Audio (Diarization)**:
    *   In Settings, select **Deepgram** as the Transcriber.
    *   Enter your Deepgram API Key.
    *   *Note: This enables "Host vs Guest" identification.*

## Troubleshooting
*   **FFmpeg Error**: Ensure FFmpeg is installed or placed in `C:\ffmpeg\bin`.
*   **Site Can't Be Reached**: Make sure `npm run dev` is running in the frontend terminal.
*   **Transcription Failed**: Check the backend terminal logs for detailed error messages.
