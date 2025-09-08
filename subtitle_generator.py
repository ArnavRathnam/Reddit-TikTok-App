import os
import requests
import time
from dotenv import load_dotenv
try:
    # Try MoviePy 2.x imports first (newer version)
    from moviepy import VideoFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
    print("Using MoviePy 2.x imports")
except ImportError:
    try:
        # Fallback to MoviePy 1.x imports (older version)
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        MOVIEPY_AVAILABLE = True
        print("Using MoviePy 1.x imports")
    except ImportError:
        MOVIEPY_AVAILABLE = False
        print("MoviePy not available")

# Load environment variables
load_dotenv()


class SubtitleGenerator:
    def __init__(self):
        self.api_key = os.getenv('ZAPCAP_API_KEY')
        self.base_url = "https://api.zapcap.ai"
        self.template_id = "6255949c-4a52-4255-8a67-39ebccfaa3ef"
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def add_subtitles(self, video_file, output_file="output_with_subtitles.mp4", chunk_duration=180):
        """
        Add animated subtitles to video using ZapCap API.
        For long videos, automatically splits into chunks for faster processing.
        
        Args:
            video_file (str): Path to the input video file
            output_file (str): Path for the output video with subtitles
            chunk_duration (int): Duration in seconds for each chunk (default: 3 minutes)
            
        Returns:
            str: Path to the output video file with subtitles
        """
        if not os.path.exists(video_file):
            print(f"Video file not found: {video_file}")
            return None
        
        if not self.api_key:
            print("ZAPCAP_API_KEY not found in environment variables")
            return None
        
        try:
            print(f"Adding subtitles to video: {video_file}")
            print(f"Using template ID: {self.template_id}")
            
            # Check if video should be processed in chunks
            if MOVIEPY_AVAILABLE:
                with VideoFileClip(video_file) as clip:
                    duration = clip.duration
                    print(f"Video duration: {duration/60:.1f} minutes")
                    
                    # If video is longer than 5 minutes, use chunked processing
                    if duration > 300:  # 5 minutes
                        print(f"🔄 Video is long ({duration/60:.1f} min), using chunked processing...")
                        return self._add_subtitles_chunked(video_file, output_file, chunk_duration)
            
            # For shorter videos, use the original single-processing method
            print("📝 Processing video in single chunk...")
            return self._add_subtitles_single(video_file, output_file)
                
        except Exception as e:
            print(f"Error adding subtitles: {e}")
            return None
    
    def _add_subtitles_single(self, video_file, output_file):
        """
        Process a single video file with subtitles (original method)
        """
        try:
            # Calculate appropriate timeout based on video duration
            timeout_minutes = self._calculate_timeout(video_file)
            print(f"Using timeout of {timeout_minutes} minutes for processing")
            
            # Step 1: Upload video
            video_id = self._upload_video(video_file)
            if not video_id:
                return None
            
            # Step 2: Create subtitle task
            task_id = self._create_subtitle_task(video_id)
            if not task_id:
                return None
            
            # Step 3: Wait for processing and get download URL
            download_url = self._wait_for_processing(video_id, task_id, max_wait_minutes=timeout_minutes)
            if not download_url:
                return None
            
            # Step 4: Download the result
            success = self._download_video(download_url, output_file)
            if success:
                print(f"✅ Subtitled video saved to: {output_file}")
                return output_file
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error in single subtitle processing: {e}")
            return None
    
    def _add_subtitles_chunked(self, video_file, output_file, chunk_duration=180):
        """
        Process a long video by splitting it into chunks, adding subtitles to each,
        then merging them back together.
        """
        if not MOVIEPY_AVAILABLE:
            print("❌ MoviePy required for chunked processing. Falling back to single processing.")
            return self._add_subtitles_single(video_file, output_file)
        
        temp_dir = "temp_subtitle_chunks"
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            with VideoFileClip(video_file) as video:
                duration = video.duration
                num_chunks = int(duration // chunk_duration) + (1 if duration % chunk_duration > 0 else 0)
                
                print(f"📂 Splitting video into {num_chunks} chunks of {chunk_duration//60} minutes each...")
                
                chunk_files = []
                subtitled_chunk_files = []
                
                # Step 1: Split video into chunks
                for i in range(num_chunks):
                    start_time = i * chunk_duration
                    end_time = min((i + 1) * chunk_duration, duration)
                    
                    chunk_filename = f"{temp_dir}/chunk_{i+1:02d}.mp4"
                    subtitled_chunk_filename = f"{temp_dir}/subtitled_chunk_{i+1:02d}.mp4"
                    
                    print(f"🔪 Creating chunk {i+1}/{num_chunks} ({start_time//60:.1f}-{end_time//60:.1f} min)...")
                    
                    chunk_clip = video.subclip(start_time, end_time)
                    chunk_clip.write_videofile(
                        chunk_filename,
                        codec='libx264',
                        audio_codec='aac',
                        verbose=False,
                        logger=None
                    )
                    chunk_clip.close()
                    
                    chunk_files.append(chunk_filename)
                    subtitled_chunk_files.append(subtitled_chunk_filename)
                
                # Step 2: Process each chunk with subtitles
                successful_chunks = []
                for i, (chunk_file, subtitled_file) in enumerate(zip(chunk_files, subtitled_chunk_files)):
                    print(f"\n📝 Processing subtitles for chunk {i+1}/{num_chunks}...")
                    
                    result = self._add_subtitles_single(chunk_file, subtitled_file)
                    if result:
                        successful_chunks.append(result)
                        print(f"✅ Chunk {i+1} processed successfully")
                    else:
                        print(f"⚠️  Chunk {i+1} failed, using original chunk")
                        # If subtitle processing fails, use original chunk
                        successful_chunks.append(chunk_file)
                
                # Step 3: Merge subtitled chunks
                print(f"\n🔗 Merging {len(successful_chunks)} chunks into final video...")
                
                clips = []
                for chunk_file in successful_chunks:
                    clip = VideoFileClip(chunk_file)
                    clips.append(clip)
                
                final_video = concatenate_videoclips(clips)
                final_video.write_videofile(
                    output_file,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
                # Cleanup
                for clip in clips:
                    clip.close()
                final_video.close()
                
                print(f"✅ Final subtitled video saved to: {output_file}")
                return output_file
                
        except Exception as e:
            print(f"❌ Error in chunked subtitle processing: {e}")
            return None
        
        finally:
            # Cleanup temporary files
            self._cleanup_temp_files(temp_dir)
    
    def _cleanup_temp_files(self, temp_dir):
        """Clean up temporary chunk files"""
        try:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"🧹 Cleaned up temporary files in {temp_dir}")
        except Exception as e:
            print(f"⚠️  Could not clean up temporary files: {e}")
    
    def _calculate_timeout(self, video_file):
        """
        Calculate appropriate timeout based on video duration
        
        Args:
            video_file (str): Path to video file
            
        Returns:
            int: Timeout in minutes
        """
        try:
            if MOVIEPY_AVAILABLE:
                with VideoFileClip(video_file) as clip:
                    duration_minutes = clip.duration / 60
                    print(f"Video duration: {duration_minutes:.1f} minutes")
                    
                    # Rule of thumb: Allow 3-5 minutes processing time per minute of video
                    # Minimum 10 minutes, maximum 60 minutes
                    timeout_minutes = max(10, min(60, int(duration_minutes * 4) + 5))
                    return timeout_minutes
            else:
                print("MoviePy not available, using default timeout")
                return 20  # Default timeout for unknown duration
        except Exception as e:
            print(f"Error calculating video duration: {e}")
            return 20  # Fallback timeout
    
    def _upload_video(self, video_file):
        """
        Upload video to ZapCap
        """
        print("📤 Uploading video to ZapCap...")
        
        try:
            # Calculate upload timeout based on file size
            file_size_mb = os.path.getsize(video_file) / (1024 * 1024)
            upload_timeout = max(300, int(file_size_mb * 30))  # 30 seconds per MB, minimum 5 minutes
            print(f"📁 File size: {file_size_mb:.1f} MB, using {upload_timeout//60} minute upload timeout")
            
            with open(video_file, 'rb') as f:
                response = requests.post(
                    f"{self.base_url}/videos",
                    headers={'x-api-key': self.api_key},
                    files={'file': f},
                    timeout=upload_timeout
                )
            
            response.raise_for_status()
            video_data = response.json()
            video_id = video_data['id']
            print(f"✅ Video uploaded successfully. Video ID: {video_id}")
            return video_id
                
        except Exception as e:
            print(f"❌ Error uploading video: {e}")
            if "timeout" in str(e).lower():
                print("💡 Upload timed out. Consider reducing video file size or checking internet connection.")
            return None
    
    def _create_subtitle_task(self, video_id):
        """
        Create subtitle generation task
        """
        print("Creating subtitle task...")
        
        task_data = {
            "templateId": self.template_id,
            "autoApprove": True,
            "language": "en"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/videos/{video_id}/task",
                headers=self.headers,
                json=task_data,
                timeout=60
            )
            
            response.raise_for_status()
            task_response = response.json()
            task_id = task_response['taskId']
            print(f"Subtitle task created. Task ID: {task_id}")
            return task_id
                
        except Exception as e:
            print(f"Error creating subtitle task: {e}")
            return None
    
    def _wait_for_processing(self, video_id, task_id, max_wait_minutes=15):
        """
        Wait for subtitle processing to complete and return download URL
        """
        print(f"Waiting for subtitle processing (timeout: {max_wait_minutes} minutes)...")
        
        max_wait_seconds = max_wait_minutes * 60
        check_interval = 10  # Check every 10 seconds for long videos
        elapsed_time = 0
        last_status = None
        consecutive_failures = 0
        
        while elapsed_time < max_wait_seconds:
            try:
                response = requests.get(
                    f"{self.base_url}/videos/{video_id}/task/{task_id}",
                    headers={'x-api-key': self.api_key},
                    timeout=30
                )
                
                response.raise_for_status()
                task_data = response.json()
                status = task_data.get('status', 'unknown')
                progress = task_data.get('progress', 0)
                
                # Only print status updates when there's a change
                if status != last_status:
                    if progress > 0:
                        print(f"Status: {status} ({progress}% complete)")
                    else:
                        print(f"Status: {status}")
                    last_status = status
                
                # Show periodic progress updates for long processing
                if elapsed_time % 60 == 0 and elapsed_time > 0:  # Every minute
                    minutes_elapsed = elapsed_time // 60
                    minutes_remaining = max_wait_minutes - minutes_elapsed
                    print(f"⏱️  Processing for {minutes_elapsed} minutes, {minutes_remaining} minutes remaining...")
                
                if status == 'completed':
                    download_url = task_data.get('downloadUrl')
                    if download_url:
                        print("✅ Subtitle processing completed!")
                        return download_url
                    else:
                        print("❌ Task completed but no download URL found")
                        return None
                elif status == 'failed':
                    error_msg = task_data.get('error', 'Unknown error')
                    print(f"❌ Subtitle processing failed: {error_msg}")
                    return None
                else:
                    # Still processing - reset failure counter on successful status check
                    consecutive_failures = 0
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                    
            except Exception as e:
                consecutive_failures += 1
                print(f"⚠️  Error checking task status (attempt {consecutive_failures}): {e}")
                
                # If we have too many consecutive failures, give up
                if consecutive_failures >= 5:
                    print("❌ Too many consecutive failures checking status. Giving up.")
                    return None
                
                # Wait longer between retries after failures
                retry_delay = min(30, check_interval * consecutive_failures)
                time.sleep(retry_delay)
                elapsed_time += retry_delay
        
        print(f"⏰ Timeout: Processing took longer than {max_wait_minutes} minutes")
        print("💡 Tip: Try processing shorter video segments or check ZapCap API status")
        return None
    
    def _download_video(self, download_url, output_file):
        """
        Download the processed video with subtitles
        """
        print(f"Downloading subtitled video...")
        
        try:
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"Download completed: {output_file}")
            return True
                
        except Exception as e:
            print(f"Error downloading video: {e}")
            return False
    
    def get_available_templates(self):
        """
        Get list of available subtitle templates
        """
        try:
            response = requests.get(
                f"{self.base_url}/templates",
                headers={'x-api-key': self.api_key},
                timeout=30
            )
            
            response.raise_for_status()
            templates = response.json()
            print("Available subtitle templates:")
            for template in templates:
                print(f"- ID: {template.get('id')} - {template.get('name')}")
            return templates
                
        except Exception as e:
            print(f"Error getting templates: {e}")
            return []


def test_subtitle_generator():
    """Test the subtitle generator with the combined video"""
    generator = SubtitleGenerator()
    
    print("TESTING SUBTITLE GENERATOR")
    print("="*50)
    
    # Check if we have a test video
    test_video = "test_combined_video.mp4"
    if not os.path.exists(test_video):
        print(f"Test video not found: {test_video}")
        print("Please run the video processor test first to create a test video.")
        return
    
    # Get available templates first
    print("Getting available templates...")
    templates = generator.get_available_templates()
    
    # Test adding subtitles with our configured template ID
    print(f"\nTesting with template ID: {generator.template_id}")
    
    result = generator.add_subtitles(
        video_file=test_video,
        output_file="test_subtitled_video.mp4"
    )
    
    if result:
        print("SUCCESS: Subtitles added to video!")
        if os.path.exists(result):
            size = os.path.getsize(result)
            print(f"Subtitled video file size: {size} bytes")
        else:
            print("ERROR: Subtitled video file not found")
    else:
        print("FAILED: Could not add subtitles")


if __name__ == "__main__":
    test_subtitle_generator()