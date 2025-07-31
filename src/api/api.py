from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Tuple
import io
import os
from gtts import gTTS
from pydub import AudioSegment
import speech_recognition as sr
from langdetect import detect, DetectorFactory
from googletrans import Translator, LANGUAGES

DetectorFactory.seed = 0

router = APIRouter()

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    lang: str = Field(default='en', min_length=2, max_length=7)

class TTS:
    def __init__(self, lang: str = 'en', output_file: str = 'output.wav'):
        # Normalize language code to lowercase
        self.lang = lang.lower()
        self.output_file = output_file

    def text_to_speech(self, text: str) -> None:
        try:
            tts = gTTS(text=text, lang=self.lang)
            tts.save(self.output_file)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS conversion failed: {str(e)}")

class STT:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.supported_languages: Dict[str, str] = {
            'en-us': 'English (US)', 'en-gb': 'English (UK)', 'es-es': 'Spanish',
            'fr-fr': 'French', 'de-de': 'German', 'it-it': 'Italian',
            'pt-br': 'Portuguese (Brazil)', 'ru-ru': 'Russian', 'ja-jp': 'Japanese',
            'ko-kr': 'Korean', 'zh-cn': 'Chinese (Simplified)', 'ar-sa': 'Arabic',
            'hi-in': 'Hindi', 'tr-tr': 'Turkish'
        }

    def get_supported_languages(self) -> List[Dict[str, str]]:
        return [{"code": code, "name": name} for code, name in self.supported_languages.items()]

    def get_language_name(self, language_code: str) -> str:
        return self.supported_languages.get(language_code.lower(), 'Unknown')

    async def speech_to_text(self, audio_file: UploadFile, language: str = "auto") -> Tuple[str, str]:
        try:
            # Normalize language code
            language = language.lower()
            if language != "auto" and language not in self.supported_languages:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported language code. Supported languages: {', '.join(self.supported_languages.keys())}"
                )

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
            raise HTTPException(status_code=400, detail="Could not understand audio")
        except sr.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Speech recognition service error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    source_lang: str = "auto"
    target_lang: str = Field(..., min_length=2, max_length=7)

class TranslationResponse(BaseModel):
    original_text: str
    source_lang: str
    target_lang: str
    translated_text: str

class SpeechToTextResponse(BaseModel):
    text: str
    language_code: str
    language_name: str

@router.post("/text-to-speech", response_class=FileResponse)
async def text_to_speech(request: TTSRequest):
    tts = TTS(lang=request.lang)
    tts.text_to_speech(request.text)
    return FileResponse(
        path=tts.output_file,
        media_type="audio/wav",
        filename=os.path.basename(tts.output_file)
    )

@router.get("/languages", response_model=List[Dict[str, str]])
async def get_supported_languages():
    return STT().get_supported_languages()

@router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(audio_file: UploadFile = File(...), language: str = "auto"):
    if not audio_file:
        raise HTTPException(status_code=400, detail="Audio file required")
    
    stt = STT()
    text, detected_language = await stt.speech_to_text(audio_file, language)
    return {
        "text": text,
        "language_code": detected_language,
        "language_name": stt.get_language_name(detected_language)
    }

@router.post("/translate", response_model=TranslationResponse)
async def translate(request: TranslationRequest):
    # Normalize language codes to lowercase
    source_lang = request.source_lang.lower()
    target_lang = request.target_lang.lower()

    if source_lang != "auto" and source_lang not in LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Invalid source language: {source_lang}")
    if target_lang not in LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Invalid target language: {target_lang}")

    translator = Translator()
    try:
        translation = translator.translate(
            request.text,
            src=source_lang,
            dest=target_lang
        )
        return {
            "original_text": request.text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "translated_text": translation.text
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Translation error: {str(e)}")

@router.post("/text-to-sql")
async def text_to_sql(question: str):
    try:
        from src.nlp.sql_agent import SQLAgent
        agent = SQLAgent()
        result = agent.query(question)
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("error_details", "Query processing failed")
            )
        
        return result
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"SQL Agent import failed: {str(e)}")
    except ValueError as ve:
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing error: {str(e)}")