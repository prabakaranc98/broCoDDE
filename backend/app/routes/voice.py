"""
BroCoDDE — Voice Transcription Endpoint
POST /voice/transcribe — accepts audio blob, uses OpenRouter audio model for ASR.
Falls back to Web Speech API client-side; this route is the server-side fallback.
"""

import base64
import json

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI

from app.config import settings
from app.models.router import OPENROUTER_BASE_URL, OPENROUTER_EXTRA_HEADERS

router = APIRouter()

# OpenRouter model with audio input support (filter by input_modalities=audio)
# GPT-4o Audio Preview is verified to accept input_audio content blocks
AUDIO_MODEL = "openai/gpt-4o-audio-preview"


@router.post("/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Accepts a WAV/MP3/WebM audio file, base64-encodes it, and sends to OpenRouter
    using the input_audio content block format. Returns the transcribed text.

    Client-side: use Web Speech API (free, instant, in-browser).
    This route: fallback for browsers without SpeechRecognition (Firefox, etc.)
    """
    if not settings.openrouter_api_key:
        raise HTTPException(status_code=402, detail="OPENROUTER_API_KEY not set — voice transcription unavailable.")

    audio_bytes = await file.read()
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    # Detect MIME type
    content_type = file.content_type or "audio/webm"
    # OpenRouter accepts: audio/wav, audio/mpeg, audio/webm
    if content_type not in ("audio/wav", "audio/mpeg", "audio/webm", "audio/mp4"):
        content_type = "audio/webm"

    client = AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers=OPENROUTER_EXTRA_HEADERS,
    )

    try:
        response = await client.chat.completions.create(
            model=AUDIO_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_b64,
                                "format": content_type.split("/")[-1],  # "webm", "wav", etc.
                            },
                        },
                        {
                            "type": "text",
                            "text": "Please transcribe this audio exactly as spoken. Return only the transcript, no commentary.",
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )
        transcript = response.choices[0].message.content or ""
        return JSONResponse({"transcript": transcript.strip()})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
