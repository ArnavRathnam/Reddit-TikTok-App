#!/usr/bin/env python3
import os
import sys
import time
import re
from datetime import datetime
from dotenv import load_dotenv

# Import our modules
from reddit_fetcher import RedditFetcher
from text_processor import TextProcessor
from tts_generator import TTSGenerator
from video_processor import VideoProcessor
from subtitle_generator import SubtitleGenerator

# Load environment variables
load_dotenv()


def print_banner():
    """Print the application banner"""
    print("=" * 60)
    print("🚀 REDDIT VIDEO CONVERTER")
    print("=" * 60)
    print("Converts Reddit posts to videos with narration!")
    print()


def check_requirements():
    """Check if all required API keys and files are present"""
    issues = []
    
    # Check API keys
    if not os.getenv('ELEVENLABS_API_KEY'):
        issues.append("❌ ELEVENLABS_API_KEY not found in .env file")
    else:
        print("✅ ElevenLabs API key found")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not found - will use basic text cleanup")
    else:
        print("✅ OpenAI API key found")
    
    if not os.getenv('ZAPCAP_API_KEY'):
        print("⚠️  ZAPCAP_API_KEY not found - subtitles will be skipped")
    else:
        print("✅ ZapCap API key found")
    
    # Check background video
    if not os.path.exists("background_video.mp4"):
        issues.append("❌ background_video.mp4 not found")
    else:
        print("✅ Background video found")
    
    if issues:
        print("\nIssues found:")
        for issue in issues:
            print(f"  {issue}")
        return False
    
    print("✅ All requirements satisfied!")
    return True


def sanitize_filename(title):
    """
    Convert Reddit post title to a safe filename
    
    Args:
        title (str): Reddit post title
        
    Returns:
        str: Safe filename (without extension)
    """
    # Remove or replace unsafe characters
    safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
    
    # Replace spaces and other characters with underscores
    safe_title = re.sub(r'[\s\-\[\](){}]+', '_', safe_title)
    
    # Remove multiple underscores
    safe_title = re.sub(r'_+', '_', safe_title)
    
    # Trim underscores from start and end
    safe_title = safe_title.strip('_')
    
    # Limit length to avoid filesystem issues
    if len(safe_title) > 100:
        safe_title = safe_title[:100].rstrip('_')
    
    # Ensure it's not empty
    if not safe_title:
        safe_title = "reddit_story"
    
    return safe_title


def cleanup_intermediate_files(audio_file):
    """
    Delete intermediate audio files after processing
    
    Args:
        audio_file (str): Path to audio file to delete
    """
    try:
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"🗑️  Cleaned up: {audio_file}")
    except Exception as e:
        print(f"⚠️  Could not delete {audio_file}: {e}")


def get_reddit_url():
    """Get Reddit URL from user input"""
    while True:
        url = input("\nEnter Reddit post URL: ").strip()
        
        if not url:
            print("Please enter a valid URL")
            continue
        
        if "reddit.com" not in url:
            print("Please enter a valid Reddit URL")
            continue
        
        return url


def process_reddit_to_video(reddit_url, use_openai=True, add_subtitles=True):
    """
    Main processing pipeline
    
    Args:
        reddit_url (str): Reddit post URL
        use_openai (bool): Whether to use OpenAI for text processing
        add_subtitles (bool): Whether to add subtitles with ZapCap
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_files = {}
    safe_title = None
    
    try:
        # Step 1: Fetch Reddit post
        print("\n🔍 Step 1: Fetching Reddit post...")
        fetcher = RedditFetcher()
        post_data = fetcher.fetch_post(reddit_url)
        
        if not post_data:
            print("❌ Failed to fetch Reddit post")
            return None
        
        print(f"✅ Fetched post: {post_data['title'][:50]}...")
        print(f"   Content length: {len(post_data['full_text'])} characters")
        
        # Create safe filename from title
        safe_title = sanitize_filename(post_data['title'])
        print(f"   Safe filename: {safe_title}")
        
        # Step 2: Process text
        print("\n✏️  Step 2: Processing text...")
        processor = TextProcessor()
        
        if use_openai and os.getenv('OPENAI_API_KEY'):
            processed_text = processor.process_text_for_narration(post_data['full_text'])
        else:
            processed_text = processor._basic_text_cleanup(post_data['full_text'])
        
        if not processed_text:
            print("❌ Text processing failed")
            return None
        
        print(f"✅ Text processed: {len(processed_text)} characters")
        
        # Step 3: Generate audio
        print("\n🎵 Step 3: Generating audio with ElevenLabs...")
        tts = TTSGenerator()
        audio_file = f"{safe_title}_audio.mp3"
        
        audio_result = tts.generate_audio(processed_text, output_file=audio_file)
        
        if not audio_result:
            print("❌ Audio generation failed")
            return None
        
        print(f"✅ Audio generated: {audio_file}")
        output_files['audio'] = audio_file
        
        # Step 4: Combine with background video
        print("\n🎬 Step 4: Combining audio with background video...")
        video_processor = VideoProcessor()
        combined_video = f"videos/{safe_title}.mp4"
        
        video_result = video_processor.combine_audio_video(
            audio_file=audio_file,
            output_file=combined_video
        )
        
        if not video_result:
            print("❌ Video combination failed")
            return None
        
        print(f"✅ Video combined: {combined_video}")
        output_files['video'] = combined_video
        
        # Step 5: Add subtitles (optional)
        final_video = combined_video
        if add_subtitles and os.getenv('ZAPCAP_API_KEY'):
            print("\n📝 Step 5: Adding subtitles with ZapCap...")
            subtitle_gen = SubtitleGenerator()
            subtitled_video = f"videos/{safe_title}_with_subtitles.mp4"
            
            subtitle_result = subtitle_gen.add_subtitles(
                video_file=combined_video,
                output_file=subtitled_video
            )
            
            if subtitle_result:
                print(f"✅ Subtitles added: {subtitled_video}")
                final_video = subtitled_video
                output_files['final_video'] = subtitled_video
            else:
                print("⚠️  Subtitle generation failed, using video without subtitles")
                output_files['final_video'] = combined_video
        else:
            print("\n⏭️  Step 5: Skipping subtitles (ZapCap not configured)")
            output_files['final_video'] = combined_video
        
        # Step 6: Generate hashtags file
        print("\n🏷️  Step 6: Generating hashtags...")
        hashtags = processor.generate_hashtags(
            post_title=post_data['title'],
            post_content=processed_text,
            subreddit=post_data['subreddit']
        )
        
        # Save hashtags to file
        hashtags_file = f"videos/{safe_title}_hashtags.txt"
        try:
            with open(hashtags_file, 'w', encoding='utf-8') as f:
                f.write(hashtags)
            print(f"✅ Hashtags saved: {hashtags_file}")
            output_files['hashtags'] = hashtags_file
        except Exception as e:
            print(f"⚠️  Could not save hashtags file: {e}")
        
        # Step 7: Clean up intermediate files
        print(f"\n🧹 Step 7: Cleaning up intermediate files...")
        cleanup_intermediate_files(audio_file)
        
        # Step 8: Final video saved
        print(f"\n💾 Step 8: Video saved to videos folder: {final_video}")
        
        # Success summary
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! Your Reddit video is ready!")
        print("=" * 60)
        print(f"📹 Final video: {final_video}")
        if 'hashtags' in output_files:
            print(f"🏷️  Hashtags: {output_files['hashtags']}")
        print(f"📊 Original text: {len(post_data['full_text'])} chars")
        print(f"🎙️  Audio duration: ~{len(processed_text) / 150:.1f} minutes")
        print(f"📁 Video saved to: {final_video}")
        print("🎬 Your video is ready to use!")
        
        return output_files
        
    except KeyboardInterrupt:
        print("\n\n❌ Process interrupted by user")
        return None
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        return None


def main():
    """Main application entry point"""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please fix the issues above before proceeding.")
        sys.exit(1)
    
    # Get Reddit URL
    reddit_url = get_reddit_url()
    
    # Ask user preferences
    print("\n⚙️  Configuration:")
    use_openai = os.getenv('OPENAI_API_KEY') is not None
    add_subtitles = os.getenv('ZAPCAP_API_KEY') is not None
    
    if use_openai:
        print("✅ Will use OpenAI for text processing")
    else:
        print("⚠️  Will use basic text cleanup (no OpenAI)")
    
    if add_subtitles:
        print("✅ Will attempt to add subtitles with ZapCap")
    else:
        print("⚠️  Will skip subtitles (no ZapCap)")
    
    # Confirm processing
    print(f"\n📍 Processing: {reddit_url}")
    confirm = input("Continue? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Processing cancelled")
        sys.exit(0)
    
    
    # Start processing
    start_time = time.time()
    result = process_reddit_to_video(
        reddit_url=reddit_url,
        use_openai=use_openai,
        add_subtitles=add_subtitles
    )
    
    if result:
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n⏱️  Total processing time: {duration:.1f} seconds")
        print("\n🎬 Your video is ready! Check the videos folder.")
    else:
        print("\n❌ Processing failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()