import os
import requests
import time
from dotenv import load_dotenv

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
    
    def add_subtitles(self, video_file, output_file="output_with_subtitles.mp4"):
        """
        Add animated subtitles to video using ZapCap API
        
        Args:
            video_file (str): Path to the input video file
            output_file (str): Path for the output video with subtitles
            
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
            
            # Step 1: Upload video
            video_id = self._upload_video(video_file)
            if not video_id:
                return None
            
            # Step 2: Create subtitle task
            task_id = self._create_subtitle_task(video_id)
            if not task_id:
                return None
            
            # Step 3: Wait for processing and get download URL
            download_url = self._wait_for_processing(video_id, task_id)
            if not download_url:
                return None
            
            # Step 4: Download the result
            success = self._download_video(download_url, output_file)
            if success:
                print(f"Subtitled video saved to: {output_file}")
                return output_file
            else:
                return None
                
        except Exception as e:
            print(f"Error adding subtitles: {e}")
            return None
    
    def _upload_video(self, video_file):
        """
        Upload video to ZapCap
        """
        print("Uploading video to ZapCap...")
        
        try:
            with open(video_file, 'rb') as f:
                response = requests.post(
                    f"{self.base_url}/videos",
                    headers={'x-api-key': self.api_key},
                    files={'file': f},
                    timeout=300  # 5 minute timeout for upload
                )
            
            response.raise_for_status()
            video_data = response.json()
            video_id = video_data['id']
            print(f"Video uploaded successfully. Video ID: {video_id}")
            return video_id
                
        except Exception as e:
            print(f"Error uploading video: {e}")
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
        print("Waiting for subtitle processing...")
        
        max_wait_seconds = max_wait_minutes * 60
        check_interval = 2  # Check every 2 seconds (like in the example)
        elapsed_time = 0
        attempts = 0
        
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
                
                print(f"Status: {status}")
                
                if status == 'completed':
                    download_url = task_data.get('downloadUrl')
                    if download_url:
                        print("Subtitle processing completed!")
                        return download_url
                    else:
                        print("Task completed but no download URL found")
                        return None
                elif status == 'failed':
                    error_msg = task_data.get('error', 'Unknown error')
                    print(f"Subtitle processing failed: {error_msg}")
                    return None
                else:
                    # Still processing
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                    attempts += 1
                    
            except Exception as e:
                print(f"Error checking task status: {e}")
                time.sleep(check_interval)
                elapsed_time += check_interval
        
        print(f"Timeout: Processing took longer than {max_wait_minutes} minutes")
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