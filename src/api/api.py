from fastapi import APIRouter, HTTPException, Path, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Tuple
import io
import os
import tempfile
import logging
from gtts import gTTS
from pydub import AudioSegment
import speech_recognition as sr
from langdetect import detect, DetectorFactory
from deep_translator import GoogleTranslator
import uuid

from src.nlp.tts import TTS
# from src.nlp.stt import STT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure consistent language detection
DetectorFactory.seed = 0

# Initialize router
router = APIRouter()

# Pydantic Models
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    lang: str = Field(default="en", pattern=r"^[a-z]{2}(-[a-zA-Z]{2})?$")

class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    source_lang: str = Field(default="auto", pattern=r"^(auto|[a-z]{2}(-[a-zA-Z]{2})?)$")
    target_lang: str = Field(..., pattern=r"^[a-z]{2}(-[a-zA-Z]{2})?$")

class SpeechToTextResponse(BaseModel):
    text: str
    language_code: str
    language_name: str

class TranslationResponse(BaseModel):
    original_text: str
    source_lang: str
    target_lang: str
    translated_text: str

class STT:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.supported_languages = {
            "en-us": "English (US)", "en-gb": "English (UK)", "es-es": "Spanish",
            "fr-fr": "French", "de-de": "German", "it-it": "Italian",
            "pt-br": "Portuguese (Brazil)", "ru-ru": "Russian", "ja-jp": "Japanese",
            "ko-kr": "Korean", "zh-cn": "Chinese (Simplified)", "ar-sa": "Arabic",
            "hi-in": "Hindi", "tr-tr": "Turkish"
        }

    def get_supported_languages(self) -> List[Dict[str, str]]:
        return [{"code": code, "name": name} for code, name in self.supported_languages.items()]

    def get_language_name(self, language_code: str) -> str:
        return self.supported_languages.get(language_code.lower(), "Unknown")

    async def speech_to_text(self, audio_file: File, language: str = "auto") -> Tuple[str, str]:
        try:
            language = language.lower()
            if language != "auto" and language not in self.supported_languages:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported language code. Supported languages: {', '.join(self.supported_languages.keys())}"
                )

            # Validate file size (e.g., max 10MB)
            if audio_file.size > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Audio file too large (max 10MB)")

            audio_bytes = await audio_file.read()
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            pcm_wav_io = io.BytesIO()
            audio_segment.export(pcm_wav_io, format="wav")
            pcm_wav_io.seek(0)

            with sr.AudioFile(pcm_wav_io) as source:
                self.recognizer.adjust_for_ambient_noise(source)
                recorded_audio = self.recognizer.record(source)

                if language == "auto":
                    text = self.recognizer.recognize_google(recorded_audio)
                    detected_language = detect(text)
                    for lang_code in self.supported_languages:
                        if lang_code.startswith(detected_language):
                            detected_language = lang_code
                            break
                    return text, detected_language
                else:
                    text = self.recognizer.recognize_google(recorded_audio, language=language)
                    return text, language

        except sr.UnknownValueError:
            logger.error("Speech recognition failed: Could not understand audio")
            raise HTTPException(status_code=400, detail="Could not understand audio")
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {str(e)}")
            raise HTTPException(status_code=502, detail=f"Speech recognition service error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in STT: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/text-to-speech", response_class=StreamingResponse)
async def text_to_speech(request: TTSRequest):
    tts = TTS(lang=request.lang)
    audio_io = await tts.text_to_speech(request.text)
    return StreamingResponse(
        audio_io,
        media_type="audio/wav",
        headers={"Content-Disposition": f"attachment; filename=output_{uuid.uuid4()}.wav"}
    )

@router.get("/languages", response_model=List[Dict[str, str]])
async def get_supported_languages():
    return STT().get_supported_languages()

@router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(
    file_path: str = Path(..., description="Path to the audio file"),
    language: str = "auto"
):
    if not os.path.exists(file_path):
        return JSONResponse(content={"error": "File not found"}, status_code=404)

    stt = STT()
    text, detected_language = await stt.speech_to_text(file_path, language)
    return {
        "text": text,
        "language_code": detected_language,
        "language_name": stt.get_language_name(detected_language)
    }

@router.post("/translate", response_model=TranslationResponse)
async def translate(
    request: TranslationRequest
):
    source_lang = request.source_lang
    target_lang = request.target_lang

    translator = GoogleTranslator(source=source_lang, target=target_lang)
    try:
        translated_text = translator.translate(request.text)
        return {
            "original_text": request.text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "translated_text": translated_text
        }
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Translation error: {str(e)}")

@router.post("/text-to-sql")
async def text_to_sql(question: str):
    try:
        from src.nlp.sql_agent import SQLAgent
        agent = SQLAgent()
        result = agent.query(question)
        
        if result.get("status") == "error":
            logger.error(f"SQL query error: {result.get('error_details', 'Unknown error')}")
            raise HTTPException(
                status_code=500,
                detail=result.get("error_details", "Query processing failed")
            )
        
        return result
        
    except ImportError as e:
        logger.error(f"SQL Agent import failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SQL Agent import failed: {str(e)}")
    except ValueError as ve:
        logger.error(f"Configuration error: {str(ve)}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(ve)}")
    except Exception as e:
        logger.error(f"Query processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing error: {str(e)}")