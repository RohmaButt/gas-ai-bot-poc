from fastapi import APIRouter, HTTPException, Path, UploadFile, File
from pydub import AudioSegment
import speech_recognition as sr
from typing import List, Dict, Tuple
import io
import os
import tempfile
import logging
from langdetect import detect, DetectorFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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