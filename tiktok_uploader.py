import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TikTokUploader:
    def __init__(self):
        self.client_key = os.getenv('TIKTOK_CLIENT_KEY')
        self.client_secret = os.getenv('TIKTOK_CLIENT_SECRET')
        self.base_url = "https://open.tiktokapis.com"
    
    def prepare_for_upload(self, video_file, title=None, description=None, hashtags=None):
        """
        Prepare video for TikTok upload
        
        Args:
            video_file (str): Path to the video file
            title (str): Video title
            description (str): Video description
            hashtags (list): List of hashtags
            
        Returns:
            dict: Prepared upload data
        """
        if not os.path.exists(video_file):
            print(f"Video file not found: {video_file}")
            return None
        
        # Get video info
        file_size = os.path.getsize(video_file)
        
        # Prepare metadata
        upload_data = {
            'video_file': video_file,
            'file_size': file_size,
            'title': title or "Reddit Story",
            'description': self._create_description(description, hashtags),
            'privacy_level': 'SELF_ONLY',  # Private by default for safety
            'disable_duet': False,
            'disable_comment': False,
            'disable_stitch': False,
            'brand_content_toggle': False
        }
        
        print("Video prepared for TikTok upload:")
        print(f"  File: {video_file}")
        print(f"  Size: {file_size} bytes ({file_size / (1024*1024):.1f} MB)")
        print(f"  Title: {upload_data['title']}")
        print(f"  Description: {upload_data['description'][:100]}...")
        
        return upload_data
    
    def _create_description(self, description, hashtags):
        """
        Create TikTok-optimized description with hashtags
        """
        if not description:
            description = "Amazing Reddit story! 📖✨"
        
        # Default hashtags for Reddit stories
        default_hashtags = [
            'reddit', 'redditstory', 'storytelling', 'viral',
            'fyp', 'foryou', 'storytime', 'interesting'
        ]
        
        # Combine provided hashtags with defaults
        if hashtags:
            all_hashtags = hashtags + default_hashtags
        else:
            all_hashtags = default_hashtags
        
        # Remove duplicates and limit to 10 hashtags
        unique_hashtags = list(dict.fromkeys(all_hashtags))[:10]
        
        # Format hashtags
        hashtag_string = ' '.join([f'#{tag}' for tag in unique_hashtags])
        
        # Combine description and hashtags
        full_description = f"{description}\n\n{hashtag_string}"
        
        # Ensure it's within TikTok's character limit (2200 characters)
        if len(full_description) > 2200:
            # Trim description and keep hashtags
            max_desc_length = 2200 - len(hashtag_string) - 3  # -3 for "\n\n"
            trimmed_description = description[:max_desc_length]
            full_description = f"{trimmed_description}...\n\n{hashtag_string}"
        
        return full_description
    
    def upload_to_tiktok(self, upload_data, access_token=None):
        """
        Upload video to TikTok using official API
        
        Note: This requires proper TikTok Developer account setup and user authorization
        
        Args:
            upload_data (dict): Prepared upload data
            access_token (str): User's TikTok access token
            
        Returns:
            dict: Upload result
        """
        if not self.client_key or not self.client_secret:
            print("TikTok API credentials not configured")
            print("This would require:")
            print("1. TikTok Developer account")
            print("2. App approval from TikTok")
            print("3. User OAuth authorization")
            return None
        
        if not access_token:
            print("Access token required for TikTok upload")
            print("User must authorize the app first")
            return None
        
        # This is a placeholder for the actual TikTok upload process
        print("TikTok upload process would involve:")
        print("1. Initialize video upload")
        print("2. Upload video chunks")
        print("3. Publish video with metadata")
        print("4. Return video URL and status")
        
        # Simulate upload result
        return {
            'success': False,
            'message': 'TikTok API upload not implemented - requires developer approval',
            'video_url': None
        }
    
    def save_for_manual_upload(self, upload_data, output_dir="ready_for_upload"):
        """
        Save video and metadata for manual TikTok upload
        
        Args:
            upload_data (dict): Prepared upload data
            output_dir (str): Directory to save files for manual upload
            
        Returns:
            str: Path to the saved files
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Copy video file to output directory
        import shutil
        video_filename = os.path.basename(upload_data['video_file'])
        output_video_path = os.path.join(output_dir, video_filename)
        
        shutil.copy2(upload_data['video_file'], output_video_path)
        
        # Create metadata file
        metadata_file = os.path.join(output_dir, "upload_info.txt")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write("TIKTOK UPLOAD INFORMATION\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Video File: {video_filename}\n")
            f.write(f"File Size: {upload_data['file_size']} bytes\n\n")
            f.write(f"TITLE:\n{upload_data['title']}\n\n")
            f.write(f"DESCRIPTION:\n{upload_data['description']}\n\n")
            f.write("UPLOAD SETTINGS:\n")
            f.write(f"Privacy: {upload_data['privacy_level']}\n")
            f.write(f"Allow Comments: {not upload_data['disable_comment']}\n")
            f.write(f"Allow Duets: {not upload_data['disable_duet']}\n")
            f.write(f"Allow Stitch: {not upload_data['disable_stitch']}\n\n")
            f.write("MANUAL UPLOAD INSTRUCTIONS:\n")
            f.write("1. Open TikTok app or web version\n")
            f.write("2. Click 'Upload' or '+' button\n")
            f.write(f"3. Select the video file: {video_filename}\n")
            f.write("4. Copy and paste the title and description above\n")
            f.write("5. Configure privacy and interaction settings\n")
            f.write("6. Post your video!\n")
        
        print(f"Files saved for manual upload in: {output_dir}")
        print(f"Video: {output_video_path}")
        print(f"Instructions: {metadata_file}")
        
        return output_dir
    
    def get_video_specs(self):
        """
        Get TikTok video specifications
        """
        specs = {
            'aspect_ratio': '9:16 (vertical)',
            'resolution': '1080x1920 (recommended)',
            'duration': '15 seconds to 10 minutes',
            'file_size': 'Max 4GB',
            'formats': ['MP4', 'MOV'],
            'title_limit': '100 characters',
            'description_limit': '2200 characters'
        }
        
        print("TikTok Video Specifications:")
        for key, value in specs.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
        return specs


def test_tiktok_uploader():
    """Test the TikTok uploader preparation"""
    uploader = TikTokUploader()
    
    print("TESTING TIKTOK UPLOADER")
    print("="*50)
    
    # Check if we have a test video
    test_video = "test_combined_video.mp4"
    if not os.path.exists(test_video):
        print(f"Test video not found: {test_video}")
        print("Please run the video processor test first.")
        return
    
    # Get TikTok specs
    uploader.get_video_specs()
    print()
    
    # Prepare video for upload
    upload_data = uploader.prepare_for_upload(
        video_file=test_video,
        title="Amazing Reddit Story - You Won't Believe What Happened!",
        description="This incredible story from Reddit will blow your mind!",
        hashtags=['trending', 'unbelievable', 'drama']
    )
    
    if upload_data:
        print("\nSUCCESS: Video prepared for TikTok upload")
        
        # Save for manual upload
        output_dir = uploader.save_for_manual_upload(upload_data)
        print(f"\nFiles ready for manual upload in: {output_dir}")
    else:
        print("FAILED: Could not prepare video for upload")


if __name__ == "__main__":
    test_tiktok_uploader()