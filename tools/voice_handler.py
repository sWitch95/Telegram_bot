import speech_recognition as sr
from gtts import gTTS
import pyttsx3
from pydub import AudioSegment
import os
import tempfile

class VoiceHandler:
    def __init__(self):
        print("🎤 Initializing Voice Handler...")
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 1.0)
        voices = self.tts_engine.getProperty('voices')
        for voice in voices:
            if 'english' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        print("✅ VoiceHandler initialized!")

    def convert_ogg_to_wav(self, ogg_path: str) -> str:
        try:
            if not os.path.exists(ogg_path):
                return None
            audio = AudioSegment.from_file(ogg_path, format="ogg")
            audio = audio.set_channels(1).set_frame_rate(16000)
            wav_path = ogg_path.replace('.ogg', '.wav')
            audio.export(wav_path, format='wav')
            return wav_path if os.path.exists(wav_path) else None
        except Exception as e:
            print(f"❌ Conversion error: {e}")
            return None

    def speech_to_text(self, audio_file_path: str) -> str:
        try:
            if audio_file_path.endswith('.ogg'):
                audio_file_path = self.convert_ogg_to_wav(audio_file_path)
                if not audio_file_path:
                    return None

            with sr.AudioFile(audio_file_path) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source)

            for lang_code in ['bn-BD', 'en-US']:
                try:
                    text = self.recognizer.recognize_google(audio, language=lang_code)
                    if text.strip():
                        return text.strip()
                except:
                    continue

            return None
        except Exception as e:
            print(f"❌ STT error: {e}")
            return None

    def text_to_speech(self, text: str) -> str:
        try:
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_audio_path = temp_audio.name
            temp_audio.close()

            if any(char in text for char in 'অআইঈউঊএঐওঔকখগঘচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহ'):
                gTTS(text=text, lang='bn').save(temp_audio_path)
            else:
                self.tts_engine.save_to_file(text, temp_audio_path)
                self.tts_engine.runAndWait()

            return temp_audio_path if os.path.exists(temp_audio_path) else None
        except Exception as e:
            print(f"❌ TTS error: {e}")
            return None

voice_handler = VoiceHandler()
