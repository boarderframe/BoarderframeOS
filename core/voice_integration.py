"""
Voice Integration System for BoarderframeOS
Provides speech-to-text and text-to-speech capabilities for agents
"""

import asyncio
import json
import logging
import os
import threading
import wave
from dataclasses import dataclass
from datetime import datetime
from queue import Queue
from typing import Any, Callable, Dict, Optional

import numpy as np
import pyaudio

# TTS providers
try:
    import pyttsx3

    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import azure.cognitiveservices.speech as speechsdk

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

try:
    from elevenlabs import generate, set_api_key, voices

    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

# STT providers
try:
    import whisper

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import speech_recognition as sr

    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class VoiceProfile:
    """Voice configuration for an agent"""

    name: str
    provider: str  # 'pyttsx3', 'azure', 'elevenlabs'
    voice_id: str
    pitch: float = 0.0
    rate: float = 1.0
    volume: float = 1.0
    emotion_baseline: float = 0.5
    language: str = "en-US"


class VoiceIntegration:
    """Manages voice capabilities for BoarderframeOS agents"""

    def __init__(self):
        self.profiles = self._initialize_profiles()
        self.tts_engines = {}
        self.stt_engine = None
        self.audio_queue = Queue()
        self.is_listening = False

        # Initialize TTS engines
        self._initialize_tts()

        # Initialize STT engine
        self._initialize_stt()

    def _initialize_profiles(self) -> Dict[str, VoiceProfile]:
        """Initialize voice profiles for core agents"""
        return {
            "solomon": VoiceProfile(
                name="Solomon",
                provider="pyttsx3",  # Default to free option
                voice_id="HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_DAVID_11.0",
                pitch=-2.0,
                rate=0.9,
                volume=1.0,
                emotion_baseline=0.7,
            ),
            "david": VoiceProfile(
                name="David",
                provider="pyttsx3",
                voice_id="HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0",
                pitch=0.0,
                rate=1.0,
                volume=1.0,
                emotion_baseline=0.6,
            ),
            "eve": VoiceProfile(
                name="Eve",
                provider="pyttsx3",
                voice_id="HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0",
                pitch=2.0,
                rate=0.95,
                volume=0.9,
                emotion_baseline=0.8,
            ),
            "adam": VoiceProfile(
                name="Adam",
                provider="pyttsx3",
                voice_id="HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_DAVID_11.0",
                pitch=-1.0,
                rate=0.95,
                volume=1.0,
                emotion_baseline=0.6,
            ),
            "bezalel": VoiceProfile(
                name="Bezalel",
                provider="pyttsx3",
                voice_id="HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_DAVID_11.0",
                pitch=0.0,
                rate=1.05,
                volume=1.0,
                emotion_baseline=0.5,
            ),
        }

    def _initialize_tts(self):
        """Initialize text-to-speech engines"""

        # Initialize pyttsx3 (free, offline)
        if PYTTSX3_AVAILABLE:
            try:
                self.tts_engines["pyttsx3"] = pyttsx3.init()
                logger.info("pyttsx3 TTS initialized")
            except Exception as e:
                logger.error(f"Failed to initialize pyttsx3: {e}")

        # Initialize Azure TTS if configured
        if AZURE_AVAILABLE and os.getenv("AZURE_SPEECH_KEY"):
            try:
                speech_config = speechsdk.SpeechConfig(
                    subscription=os.getenv("AZURE_SPEECH_KEY"),
                    region=os.getenv("AZURE_SPEECH_REGION", "eastus"),
                )
                self.tts_engines["azure"] = speech_config
                logger.info("Azure TTS initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Azure TTS: {e}")

        # Initialize ElevenLabs if configured
        if ELEVENLABS_AVAILABLE and os.getenv("ELEVENLABS_API_KEY"):
            try:
                set_api_key(os.getenv("ELEVENLABS_API_KEY"))
                self.tts_engines["elevenlabs"] = True
                logger.info("ElevenLabs TTS initialized")
            except Exception as e:
                logger.error(f"Failed to initialize ElevenLabs: {e}")

    def _initialize_stt(self):
        """Initialize speech-to-text engine"""

        # Try Whisper first (best quality)
        if WHISPER_AVAILABLE:
            try:
                # Use base model for speed
                self.stt_engine = whisper.load_model("base")
                self.stt_type = "whisper"
                logger.info("Whisper STT initialized")
                return
            except Exception as e:
                logger.error(f"Failed to initialize Whisper: {e}")

        # Fallback to speech_recognition
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                self.stt_engine = sr.Recognizer()
                self.stt_type = "speech_recognition"
                logger.info("Speech Recognition STT initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Speech Recognition: {e}")

    async def text_to_speech(
        self,
        text: str,
        agent_name: str,
        emotion: Optional[float] = None,
        save_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """Convert text to speech for an agent"""

        if agent_name not in self.profiles:
            logger.error(f"No voice profile for agent: {agent_name}")
            return None

        profile = self.profiles[agent_name]
        provider = profile.provider

        # Use emotion if provided, otherwise use baseline
        emotion_value = emotion if emotion is not None else profile.emotion_baseline

        try:
            if provider == "pyttsx3" and "pyttsx3" in self.tts_engines:
                return await self._pyttsx3_tts(text, profile, save_path)

            elif provider == "azure" and "azure" in self.tts_engines:
                return await self._azure_tts(text, profile, emotion_value, save_path)

            elif provider == "elevenlabs" and "elevenlabs" in self.tts_engines:
                return await self._elevenlabs_tts(
                    text, profile, emotion_value, save_path
                )

            else:
                # Fallback to pyttsx3
                if "pyttsx3" in self.tts_engines:
                    logger.warning(f"Falling back to pyttsx3 for {agent_name}")
                    return await self._pyttsx3_tts(text, profile, save_path)
                else:
                    logger.error("No TTS engine available")
                    return None

        except Exception as e:
            logger.error(f"TTS error for {agent_name}: {e}")
            return None

    async def _pyttsx3_tts(
        self, text: str, profile: VoiceProfile, save_path: Optional[str] = None
    ) -> Optional[bytes]:
        """Generate speech using pyttsx3"""

        engine = self.tts_engines["pyttsx3"]

        # Configure voice
        voices = engine.getProperty("voices")

        # Try to find matching voice
        for voice in voices:
            if profile.voice_id in voice.id:
                engine.setProperty("voice", voice.id)
                break

        # Set properties
        engine.setProperty("rate", int(150 * profile.rate))
        engine.setProperty("volume", profile.volume)

        # Generate speech
        if save_path:
            engine.save_to_file(text, save_path)
            engine.runAndWait()

            # Read the file
            with open(save_path, "rb") as f:
                audio_data = f.read()
            return audio_data
        else:
            # Play directly
            engine.say(text)
            engine.runAndWait()
            return b""  # Return empty bytes for direct playback

    async def _azure_tts(
        self,
        text: str,
        profile: VoiceProfile,
        emotion: float,
        save_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """Generate speech using Azure Cognitive Services"""

        speech_config = self.tts_engines["azure"]

        # Configure voice
        speech_config.speech_synthesis_voice_name = profile.voice_id

        # Create SSML with emotion
        ssml = f"""
        <speak version='1.0' xml:lang='{profile.language}'>
            <voice name='{profile.voice_id}'>
                <prosody rate='{profile.rate}' pitch='{profile.pitch}Hz' volume='{profile.volume}'>
                    {text}
                </prosody>
            </voice>
        </speak>
        """

        # Configure output
        if save_path:
            audio_config = speechsdk.AudioOutputConfig(filename=save_path)
        else:
            audio_config = speechsdk.AudioOutputConfig(use_default_speaker=True)

        # Create synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )

        # Generate speech
        result = synthesizer.speak_ssml_async(ssml).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        else:
            logger.error(f"Azure TTS failed: {result.reason}")
            return None

    async def _elevenlabs_tts(
        self,
        text: str,
        profile: VoiceProfile,
        emotion: float,
        save_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """Generate speech using ElevenLabs"""

        # Generate audio
        audio = generate(
            text=text, voice=profile.voice_id, model="eleven_monolingual_v1"
        )

        audio_data = b"".join(audio)

        if save_path:
            with open(save_path, "wb") as f:
                f.write(audio_data)

        return audio_data

    async def speech_to_text(
        self, audio_data: Optional[bytes] = None, duration: int = 5
    ) -> Optional[str]:
        """Convert speech to text"""

        if self.stt_type == "whisper":
            return await self._whisper_stt(audio_data, duration)
        elif self.stt_type == "speech_recognition":
            return await self._sr_stt(audio_data, duration)
        else:
            logger.error("No STT engine available")
            return None

    async def _whisper_stt(
        self, audio_data: Optional[bytes] = None, duration: int = 5
    ) -> Optional[str]:
        """Use Whisper for speech recognition"""

        if audio_data:
            # Save to temporary file
            temp_path = "/tmp/temp_audio.wav"
            with open(temp_path, "wb") as f:
                f.write(audio_data)

            # Transcribe
            result = self.stt_engine.transcribe(temp_path)
            return result["text"]
        else:
            # Record audio
            audio_data = await self._record_audio(duration)
            if audio_data:
                return await self._whisper_stt(audio_data)
            return None

    async def _sr_stt(
        self, audio_data: Optional[bytes] = None, duration: int = 5
    ) -> Optional[str]:
        """Use speech_recognition for STT"""

        recognizer = self.stt_engine

        if not audio_data:
            # Record from microphone
            with sr.Microphone() as source:
                logger.info(f"Listening for {duration} seconds...")
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=duration)
        else:
            # Use provided audio
            audio = sr.AudioData(audio_data, 16000, 2)

        try:
            # Try Google Speech Recognition (free)
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"STT error: {e}")
            return None

    async def _record_audio(self, duration: int) -> Optional[bytes]:
        """Record audio from microphone"""

        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000

        p = pyaudio.PyAudio()

        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )

        logger.info(f"Recording for {duration} seconds...")
        frames = []

        for _ in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)

        logger.info("Recording complete")

        stream.stop_stream()
        stream.close()
        p.terminate()

        # Convert to WAV format
        wf = wave.open("/tmp/temp_recording.wav", "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
        wf.close()

        with open("/tmp/temp_recording.wav", "rb") as f:
            return f.read()

    def start_continuous_listening(self, callback: Callable[[str], None]):
        """Start continuous speech recognition"""

        if not SPEECH_RECOGNITION_AVAILABLE:
            logger.error("Speech recognition not available")
            return

        self.is_listening = True

        def listen_thread():
            recognizer = sr.Recognizer()
            mic = sr.Microphone()

            with mic as source:
                recognizer.adjust_for_ambient_noise(source)

            while self.is_listening:
                try:
                    with mic as source:
                        audio = recognizer.listen(
                            source, timeout=1, phrase_time_limit=5
                        )

                    text = recognizer.recognize_google(audio)
                    callback(text)

                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    logger.error(f"Listening error: {e}")

        thread = threading.Thread(target=listen_thread, daemon=True)
        thread.start()

    def stop_continuous_listening(self):
        """Stop continuous speech recognition"""
        self.is_listening = False

    def update_voice_profile(self, agent_name: str, **kwargs):
        """Update voice profile settings"""

        if agent_name not in self.profiles:
            logger.error(f"No profile for agent: {agent_name}")
            return

        profile = self.profiles[agent_name]

        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        logger.info(f"Updated voice profile for {agent_name}")


# Singleton instance
_voice_instance = None


def get_voice_integration() -> VoiceIntegration:
    """Get or create the singleton voice integration instance"""
    global _voice_instance
    if _voice_instance is None:
        _voice_instance = VoiceIntegration()
    return _voice_instance
