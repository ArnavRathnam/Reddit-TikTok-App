import os
import math
try:
    from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        # Fallback for older MoviePy versions
        from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
        MOVIEPY_AVAILABLE = True
    except ImportError:
        print("MoviePy not available")
        MOVIEPY_AVAILABLE = False


class VideoProcessor:
    def __init__(self):
        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy is required for video processing")
        self.background_video_path = "background_video.mp4"
    
    def combine_audio_video(self, audio_file, output_file="output_video.mp4", target_aspect_ratio=(9, 16)):
        """
        Combine background video with generated audio
        
        Args:
            audio_file (str): Path to the audio file
            output_file (str): Output video filename
            target_aspect_ratio (tuple): Target aspect ratio (width, height) for TikTok (9:16)
            
        Returns:
            str: Path to the output video file
        """
        if not os.path.exists(self.background_video_path):
            print(f"Background video not found: {self.background_video_path}")
            return None
        
        if not os.path.exists(audio_file):
            print(f"Audio file not found: {audio_file}")
            return None
        
        try:
            print("Loading background video and audio...")
            
            # Load background video and audio
            video_clip = VideoFileClip(self.background_video_path)
            audio_clip = AudioFileClip(audio_file)
            
            print(f"Background video duration: {video_clip.duration:.2f} seconds")
            print(f"Audio duration: {audio_clip.duration:.2f} seconds")
            print(f"Original video resolution: {video_clip.size}")
            
            # Get audio duration
            audio_duration = audio_clip.duration
            
            # Prepare background video to match audio duration
            video_clip = self._prepare_background_video(video_clip, audio_duration, target_aspect_ratio)
            
            # Remove original audio and add new audio
            video_clip = video_clip.without_audio()
            final_clip = video_clip.with_audio(audio_clip)
            
            print(f"Writing final video to: {output_file}")
            
            # Write the final video optimized for TikTok
            final_clip.write_videofile(
                output_file,
                codec='libx264',
                audio_codec='aac',
                bitrate='8000k',
                fps=30,
                preset='medium'
            )
            
            # Clean up
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            
            print(f"Video successfully created: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"Error combining video and audio: {e}")
            return None
    
    def _prepare_background_video(self, video_clip, target_duration, target_aspect_ratio):
        """
        Prepare background video: loop if needed, resize for TikTok format
        """
        # Calculate target resolution for TikTok (9:16 aspect ratio)
        target_width, target_height = self._calculate_tiktok_resolution(video_clip.size, target_aspect_ratio)
        
        print(f"Target resolution for TikTok: {target_width}x{target_height}")
        
        # Resize video to TikTok format
        video_clip = video_clip.resized((target_width, target_height))
        
        # Loop video if audio is longer than video
        if target_duration > video_clip.duration:
            loops_needed = math.ceil(target_duration / video_clip.duration)
            print(f"Looping background video {loops_needed} times to match audio duration")
            
            # Create looped video
            video_clips = [video_clip] * loops_needed
            looped_video = CompositeVideoClip([clip.set_start(i * video_clip.duration) 
                                               for i, clip in enumerate(video_clips)])
            
            # Trim to exact audio duration  
            looped_video = looped_video.subclipped(0, target_duration)
            return looped_video
        else:
            # Trim video to match audio duration
            print("Trimming background video to match audio duration")
            return video_clip.subclipped(0, target_duration)
    
    def _calculate_tiktok_resolution(self, original_size, target_aspect_ratio):
        """
        Calculate optimal resolution for TikTok format (9:16)
        """
        original_width, original_height = original_size
        target_width_ratio, target_height_ratio = target_aspect_ratio
        
        # Common TikTok resolutions
        tiktok_resolutions = [
            (1080, 1920),  # Full HD
            (720, 1280),   # HD
            (540, 960),    # Medium
        ]
        
        # Choose resolution based on original video quality
        if original_width >= 1080:
            return tiktok_resolutions[0]
        elif original_width >= 720:
            return tiktok_resolutions[1]
        else:
            return tiktok_resolutions[2]
    
    def get_video_info(self, video_path=None):
        """
        Get information about a video file
        """
        if video_path is None:
            video_path = self.background_video_path
        
        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return None
        
        try:
            clip = VideoFileClip(video_path)
            info = {
                'duration': clip.duration,
                'fps': clip.fps,
                'size': clip.size,
                'aspect_ratio': clip.size[0] / clip.size[1]
            }
            clip.close()
            
            print(f"Video Info for {video_path}:")
            print(f"  Duration: {info['duration']:.2f} seconds")
            print(f"  FPS: {info['fps']}")
            print(f"  Resolution: {info['size'][0]}x{info['size'][1]}")
            print(f"  Aspect Ratio: {info['aspect_ratio']:.2f}")
            
            return info
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None


def test_video_processor():
    """Test the video processor with background video info"""
    processor = VideoProcessor()
    
    print("TESTING VIDEO PROCESSOR")
    print("="*50)
    
    # Check if background video exists
    if not os.path.exists(processor.background_video_path):
        print(f"Background video not found: {processor.background_video_path}")
        return
    
    # Get video info
    info = processor.get_video_info()
    
    if info:
        print("SUCCESS: Background video loaded and analyzed")
        
        # Test with dummy audio file (create a short silent audio)
        try:
            try:
                from moviepy import AudioClip
            except ImportError:
                from moviepy.editor import AudioClip
            
            # Create 5-second silent audio for testing
            silent_audio = AudioClip(make_frame=lambda t: [0, 0], duration=5, fps=44100)
            test_audio_file = "test_silent_audio.mp3"
            silent_audio.write_audiofile(test_audio_file, verbose=False, logger=None)
            silent_audio.close()
            
            print(f"\nTesting video-audio combination with 5-second silent audio...")
            
            # Test combining
            output_video = processor.combine_audio_video(
                audio_file=test_audio_file,
                output_file="test_output_video.mp4"
            )
            
            if output_video and os.path.exists(output_video):
                print(f"SUCCESS: Test video created at {output_video}")
                
                # Get info of the output video
                print("\nOutput video info:")
                processor.get_video_info(output_video)
            else:
                print("FAILED: Could not create test video")
            
            # Clean up test files
            if os.path.exists(test_audio_file):
                os.remove(test_audio_file)
                
        except Exception as e:
            print(f"Error during video processing test: {e}")
    else:
        print("FAILED: Could not analyze background video")


if __name__ == "__main__":
    test_video_processor()