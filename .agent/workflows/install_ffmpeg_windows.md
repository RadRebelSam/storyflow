---
description: Install FFmpeg on Windows
---

# Installing FFmpeg on Windows

StoryFlow needs FFmpeg to process audio for Deepgram (Diarization).

## Option 1: Automatic Install (Recommended)

// turbo
1. Run the following command in your terminal (PowerShell):
   ```powershell
   winget install "FFmpeg (Essentials Build)"
   ```
2. **Restart your terminal** (or VS Code) to refresh the system PATH.
3. Verify installation:
   ```powershell
   ffmpeg -version
   ```

## Option 2: Manual Install

1. Download the build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z).
2. Extract the folder to `C:\ffmpeg`.
3. Add `C:\ffmpeg\bin` to your System Environment Variables -> Path.
4. Restart your computer.
