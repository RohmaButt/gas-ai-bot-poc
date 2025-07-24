import speech_recognition as sr
from langdetect import detect, DetectorFactory
from fastapi import UploadFile, File, HTTPException, APIRouter
import io
from pydub import AudioSegment
from typing import Dict, Tuple, List

DetectorFactory.seed = 0

router = APIRouter()

class STT:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Dictionary of supported languages with their codes and names
        self.supported_languages: Dict[str, str] = {
            'en-US': 'English (US)',
            'en-GB': 'English (UK)',
            'es-ES': 'Spanish',
            'fr-FR': 'French',
            'de-DE': 'German',
            'it-IT': 'Italian',
            'pt-BR': 'Portuguese (Brazil)',
            'ru-RU': 'Russian',
            'ja-JP': 'Japanese',
            'ko-KR': 'Korean',
            'zh-CN': 'Chinese (Simplified)',
            'ar-SA': 'Arabic',
            'hi-IN': 'Hindi',
            'tr-TR': 'Turkish'
        }

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get list of supported languages for speech recognition.
        
        Returns:
            List[Dict[str, str]]: List of languages with their codes and names
        """
        return [{"code": code, "name": name} for code, name in self.supported_languages.items()]

    def get_language_name(self, language_code: str) -> str:
        """
        Get the full name of a language from its code.
        
        Args:
            language_code (str): The language code (e.g., 'en-US')
            
        Returns:
            str: The full name of the language or 'Unknown' if not found
        """
        return self.supported_languages.get(language_code, 'Unknown')

    async def speech_to_text(self, audio_file: UploadFile, language="auto") -> Tuple[str, str]:
        """
        Convert speech from an audio file to text with language support.
        
        Args:
            audio_file (UploadFile): The uploaded audio file
            language (str): Language code for recognition (e.g., 'en-US', 'es-ES', etc.)
                          Use 'auto' for automatic language detection
        
        Returns:
            Tuple[str, str]: (recognized text, detected/used language code)
            
        Raises:
            HTTPException: If speech recognition fails or language is not supported
        """
        try:
            # Validate language code if not auto
            if language != "auto" and language not in self.supported_languages:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported language code. Supported languages are: {', '.join(self.supported_languages.keys())}"
                )

            # Read uploaded file bytes
            audio_bytes = await audio_file.read()

            # Convert to proper PCM WAV using pydub
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            pcm_wav_io = io.BytesIO()
            audio_segment.export(pcm_wav_io, format="wav")
            pcm_wav_io.seek(0)

            # Now read using SpeechRecognition
            with sr.AudioFile(pcm_wav_io) as source:
                self.recognizer.adjust_for_ambient_noise(source)
                recorded_audio = self.recognizer.record(source)

                if language == "auto":
                    # Try with English first, then detect language from text
                    text = self.recognizer.recognize_google(recorded_audio)
                    detected_language = detect(text)
                    # Map detected language to full language code if possible
                    for lang_code in self.supported_languages:
                        if lang_code.startswith(detected_language):
                            detected_language = lang_code
                            break
                    # convert only the chinese LN into the Big5 encoding
                    if detected_language == 'zh-CN':
                        text = text.encode('big5', errors='ignore').decode('big5')
                    return text, detected_language
                else:
                    if language == 'zh-CN':
                        # Special handling for Chinese to Big5 encoding
                        text = self.recognizer.recognize_google(recorded_audio, language=language)
                        text = text.encode('big5', errors='ignore').decode('big5')
                        return text, language

        except sr.UnknownValueError:
            raise HTTPException(status_code=400, detail="Could not understand the audio. Please speak clearly and try again.")
        except sr.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Speech recognition service error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")