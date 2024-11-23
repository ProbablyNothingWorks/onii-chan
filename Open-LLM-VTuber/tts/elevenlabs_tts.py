from typing import Optional
from elevenlabs import Voice, VoiceSettings, play
from elevenlabs.client import ElevenLabs
from .tts_interface import TTSInterface
import os
from loguru import logger

class ElevenLabsTTS(TTSInterface):
    def __init__(
        self,
        api_key: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default voice ID
        model_id: str = "eleven_monolingual_v1",
        stability: float = 0.71,
        similarity_boost: float = 0.5,
        style: float = 0.0,
        use_speaker_boost: bool = True,
    ):
        """
        Initialize ElevenLabs TTS engine.
        
        Args:
            api_key: Your ElevenLabs API key
            voice_id: The voice ID to use (default is Rachel)
            model_id: The model to use for synthesis
            stability: Voice stability (0-1)
            similarity_boost: Voice similarity boost (0-1)
            style: Style control (0-1)
            use_speaker_boost: Whether to use speaker boost
        """
        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self.model_id = model_id
        self.voice_settings = VoiceSettings(
            stability=stability,
            similarity_boost=similarity_boost,
            style=style,
            use_speaker_boost=use_speaker_boost
        )

    def generate_audio(self, text: str, file_name_no_ext: str = "temp") -> Optional[str]:
        """Generate audio file from text"""
        if not text:
            return None
            
        output_path = f"cache/{file_name_no_ext}.mp3"
        os.makedirs("cache", exist_ok=True)

        try:
            # Get the audio generator
            audio_generator = self.client.generate(
                text=text,
                voice=Voice(
                    voice_id=self.voice_id,
                    settings=self.voice_settings
                ),
                model=self.model_id
            )
            
            # Collect all the audio bytes
            audio_bytes = b''.join(chunk for chunk in audio_generator)
            
            # Save the audio
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
                
            return output_path
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS generation failed: {e}")
            return None

    def play_audio_file_local(self, file_path: str) -> None:
        """Play the audio file locally - not needed for web interface"""
        pass

    def remove_file(self, file_path: str, verbose: bool = False) -> None:
        """Remove the generated audio file"""
        try:
            os.remove(file_path)
            if verbose:
                print(f"Removed file: {file_path}")
        except Exception as e:
            if verbose:
                print(f"Error removing file {file_path}: {e}") 