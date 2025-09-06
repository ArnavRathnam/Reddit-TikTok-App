import os
import io
from elevenlabs import VoiceSettings, stream
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TTSGenerator:
    def __init__(self):
        self.client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
        
        # Default voice settings optimized for storytelling
        self.voice_settings = VoiceSettings(
            stability=0.75,
            similarity_boost=0.75,
            style=0.4,
            use_speaker_boost=True
        )
    
    def generate_audio(self, text, voice_id="JBFqnCBsd6RMkjVDRZzb", output_file="output_audio.mp3"):
        """
        Convert text to speech using ElevenLabs API
        
        Args:
            text (str): Text to convert to speech
            voice_id (str): ElevenLabs voice ID (default is Rachel)
            output_file (str): Output filename for the audio
            
        Returns:
            str: Path to the generated audio file
        """
        if not text:
            print("No text provided for TTS generation")
            return None
        
        try:
            print(f"Generating audio for {len(text)} characters of text...")
            print(f"Using voice ID: {voice_id}")
            
            # For very long texts, we might need to handle chunking
            if len(text) > 50000:  # ElevenLabs limit
                return self._generate_long_audio(text, voice_id, output_file)
            
            # Generate the audio
            audio_stream = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                voice_settings=self.voice_settings,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            
            # Save the audio to file
            with open(output_file, "wb") as f:
                for chunk in audio_stream:
                    f.write(chunk)
            
            print(f"Audio successfully generated: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None
    
    def _generate_long_audio(self, text, voice_id, output_file):
        """
        Handle very long text by chunking it into smaller pieces
        """
        print("Text is very long, chunking into smaller pieces...")
        
        # Split text into chunks at sentence boundaries
        chunks = self._split_text_into_chunks(text, max_chars=40000)
        audio_files = []
        
        for i, chunk in enumerate(chunks):
            chunk_file = f"temp_chunk_{i}.mp3"
            try:
                audio_stream = self.client.text_to_speech.convert(
                    text=chunk,
                    voice_id=voice_id,
                    voice_settings=self.voice_settings,
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128"
                )
                
                with open(chunk_file, "wb") as f:
                    for audio_chunk in audio_stream:
                        f.write(audio_chunk)
                
                audio_files.append(chunk_file)
                print(f"Generated chunk {i+1}/{len(chunks)}")
                
            except Exception as e:
                print(f"Error generating chunk {i}: {e}")
                # Clean up any temporary files
                for temp_file in audio_files:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                return None
        
        # Combine all audio files
        combined_file = self._combine_audio_files(audio_files, output_file)
        
        # Clean up temporary files
        for temp_file in audio_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        return combined_file
    
    def _split_text_into_chunks(self, text, max_chars=40000):
        """
        Split text into chunks at sentence boundaries
        """
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Add the sentence to current chunk if it fits
            if len(current_chunk + sentence + '. ') <= max_chars:
                current_chunk += sentence + '. '
            else:
                # Start new chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _combine_audio_files(self, audio_files, output_file):
        """
        Combine multiple audio files using MoviePy
        """
        try:
            from moviepy.audio.io.AudioFileClip import AudioFileClip
            from moviepy.audio.AudioClip import concatenate_audioclips
            
            audio_clips = [AudioFileClip(f) for f in audio_files]
            combined_audio = concatenate_audioclips(audio_clips)
            combined_audio.write_audiofile(output_file)
            
            # Clean up audio clips
            for clip in audio_clips:
                clip.close()
            combined_audio.close()
            
            print(f"Combined audio saved to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"Error combining audio files: {e}")
            return None
    
    def get_available_voices(self):
        """
        Get list of available voices from ElevenLabs
        """
        try:
            voices = self.client.voices.get_all()
            print("Available voices:")
            for voice in voices.voices:
                print(f"- {voice.name}: {voice.voice_id}")
            return voices.voices
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return []


def test_tts():
    """Test the TTS generator with sample text"""
    tts = TTSGenerator()
    
    # Test with sample text
    sample_text = """Hello, this is a test of the ElevenLabs text to speech system. 
    This sample will help us verify that the audio generation is working properly. 
    The voice should sound clear and natural."""
    
    print("TESTING TTS GENERATOR")
    print("="*50)
    print("Sample text:", sample_text)
    print("\nGenerating audio...")
    
    audio_file = tts.generate_audio(
        text=sample_text,
        output_file="test_audio.mp3"
    )
    
    if audio_file:
        print(f"SUCCESS: Audio generated at {audio_file}")
        print("You can play this file to test the audio quality.")
    else:
        print("FAILED: Could not generate audio")


if __name__ == "__main__":
    test_tts()