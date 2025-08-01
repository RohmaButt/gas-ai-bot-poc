import gtts
import os
from pydub import AudioSegment
import io

class TTS:
    """
    Text-to-Speech (TTS) class using gTTS (Google Text-to-Speech).
    """
    def __init__(self, lang='en', output_file='output.wav'):
        self.lang = lang
        self.output_file = output_file

    async def text_to_speech(self, text):
        """ 
            Convert text to speech and save it to a file.
        Args:
            text (str): The text to convert to speech.
        Returns:
            None
        """
        try:
            # Generate speech using gTTS
            tts = gtts.gTTS(text, lang=self.lang)
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            audio_io.seek(0)
            return audio_io
        except Exception as e:
            print(f"Error during text-to-speech conversion: {e}")


# if __name__ == "__main__":
#     tts = TTS(lang='en')
#     text = "Hello, this is a test of the text-to-speech functionality."
#     tts.text_to_speech(text)

    # tts = TTS(lang='zh-CN')
    # text = "你好，这是文本转语音功能的测试。"
    # output_file = "output_zh.wav"
    # tts.text_to_speech(text, output_file)
    
