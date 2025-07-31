from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi import UploadFile, File
from pydantic import BaseModel
from googletrans import Translator, LANGUAGES

from src.nlp.tts import TTS
from src.nlp.stt import STT
from src.database.database import create_connection
# SQL Agent is imported in the endpoint to ensure lazy loading
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
    Convert a natural language question to SQL using SQLAgent.

    Args:
        question (str): The natural language question

    Returns:
        dict: Contains the SQL query, results, and natural language response
    """
    try:
        # Initialize SQL Agent
        from src.nlp.sql_agent import SQLAgent
        agent = SQLAgent()
        
    except ValueError as ve:
        # Handle missing environment variables
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: {str(ve)}"
        )
    except Exception as init_error:
        # Handle other initialization errors
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize SQL Agent: {str(init_error)}"
        )
        
    try:
        # Process the question
        result = agent.query(question)
        
        # Check for errors
        if result["status"] == "error":
            raise HTTPException(
                status_code=500, 
                detail=result["error_details"] if "error_details" in result else "Query processing failed"
            )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle query processing errors
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )
    
class TranslationRequest(BaseModel):
    text: str
    source_lang: str = "auto"  # Default to auto-detect
    target_lang: str

def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    try:
        # Validate language codes
        if source_lang != "auto" and source_lang not in LANGUAGES:
            raise ValueError(f"Invalid source language: {source_lang}")
        if target_lang not in LANGUAGES:
            raise ValueError(f"Invalid target language: {target_lang}")
        
        translator = Translator()
        translation = translator.translate(text, src=source_lang, dest=target_lang)
        return translation.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Translation error: {str(e)}")

# Endpoint to translate text
@router.post("/translate/", response_model=dict)
async def translate(request: TranslationRequest):
    try:
        translated_text = translate_text(request.text, request.source_lang, request.target_lang)
        return {
            "original_text": request.text,
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
            "translated_text": translated_text
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
