from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi import UploadFile, File

from src.nlp.tts import TTS
from src.nlp.stt import STT
from src.nlp.vanna_module import get_response
from src.database.database import create_connection
import os

router = APIRouter()

@router.post("/text-to-speech/")
async def text_to_speech(text: str, lang: str = 'en'):
    """
    Convert text to speech and save it to a file.
    
    Args:
        text (str): The text to convert to speech.
        lang (str): Language code for the speech (default: 'en').
    
    Returns:
        FileResponse: Response containing the audio file.
    """
    tts = TTS(lang=lang)
    try:
        tts.text_to_speech(text)
        return FileResponse(tts.output_file, media_type="audio/wav", filename=tts.output_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/languages/")
async def get_supported_languages():
    """
    Get list of supported languages for speech recognition.
    
    Returns:
        dict: List of supported languages with their codes and names
    """
    stt = STT()
    return {"languages": stt.get_supported_languages()}

@router.post("/speech-to-text/")
async def speech_to_text(
    audio_file: UploadFile = File(...),
    language: str = "auto"
):
    """
    Convert speech from an audio file to text with language support.
    
    Args:
        audio_file (UploadFile): The uploaded audio file
        language (str): Language code for recognition (e.g., 'en-US', 'es-ES')
                       Use 'auto' for automatic language detection
    
    Returns:
        dict: Contains recognized text, language code, and language name
    """
    stt = STT()

    if not audio_file:
        raise HTTPException(status_code=400, detail="Audio file must be provided.")

    text, detected_language = await stt.speech_to_text(audio_file, language)
    language_name = stt.get_language_name(detected_language)
    
    return {
        "text": text,
        "language_code": detected_language,
        "language_name": language_name
    }


@router.post("/text-to-sql/")
async def text_to_sql(question: str):
    """
    Convert a natural language question to SQL using Vanna.

    Args:
        question (str): The natural language question

    Returns:
        dict: Contains the generated SQL query or an error message
    """
    conn = None
    try:
        conn = create_connection(r"retail.db")
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed.")
        
        sql_query = get_response(question)
        return {"sql_query": sql_query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()
