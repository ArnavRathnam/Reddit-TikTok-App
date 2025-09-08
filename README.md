# Reddit Video Converter 🚀

Convert Reddit posts into engaging videos with AI narration and animated subtitles!

## Features ✨

- **Reddit Post Fetching**: Automatically extracts content from Reddit URLs
- **AI Text Processing**: Uses OpenAI GPT to clean and optimize text for narration
- **High-Quality Narration**: ElevenLabs text-to-speech with natural voices
- **Video Processing**: Combines narration with background video (9:16 aspect ratio)
- **Animated Subtitles**: ZapCap integration for professional subtitle generation
- **Smart Hashtag Generation**: AI-powered hashtag creation with required #reddit and #redditstories tags

## Setup Instructions 🔧

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```bash
# Required
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Optional (for better text processing)
OPENAI_API_KEY=your_openai_api_key_here

# Optional (for subtitles)
ZAPCAP_API_KEY=your_zapcap_api_key_here
```

### 3. Add Background Video

Place your background video file as `background_video.mp4` in the project directory. The video should be:
- Vertical format (9:16 aspect ratio preferred)
- High quality (1080p recommended)
- Engaging content (satisfying videos, nature scenes, etc.)

## Usage 🎬

### Basic Usage

Run the main script:
```bash
python3 main.py
```

The script will:
1. Ask for a Reddit post URL
2. Check your configuration
3. Process the post through the complete pipeline
4. Create a video and save it to the videos folder

### Example Reddit URLs

The app works best with story-heavy subreddits like:
- r/BestofRedditorUpdates
- r/AmItheAsshole
- r/relationships
- r/tifu
- r/MaliciousCompliance

### Testing Individual Components

Each component can be tested separately:

```bash
# Test Reddit fetching
python3 reddit_fetcher.py

# Test text processing
python3 text_processor.py

# Test TTS generation
python3 tts_generator.py

# Test video processing
python3 video_processor.py

# Test subtitle generation
python3 subtitle_generator.py
```

## How It Works 🔄

1. **Reddit Fetching**: Adds `.json` to Reddit URL and extracts post content
2. **Text Processing**: Extracts title and story, cleans Reddit markdown and optimizes for speech
3. **Audio Generation**: Converts title + story to natural speech using ElevenLabs
4. **Video Combination**: Merges audio with background video, loops if needed
5. **Subtitle Addition**: Adds animated subtitles using ZapCap (optional) - long videos automatically split into chunks
6. **Hashtag Generation**: Creates relevant hashtags using AI based on post content
7. **Video Storage**: Saves final videos and hashtags to the videos folder

## File Structure 📁

```
reddit_tiktok_app/
├── main.py                 # Main application
├── reddit_fetcher.py       # Reddit API integration
├── text_processor.py       # OpenAI text processing
├── tts_generator.py        # ElevenLabs TTS
├── video_processor.py      # Video/audio combination
├── subtitle_generator.py   # ZapCap subtitles
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
├── background_video.mp4   # Your background video
└── README.md             # This file
```

## Output Files 📤

The app creates files named after the story title in the videos folder:
- `videos/Story_Title.mp4` - Final video (with or without subtitles)
- `videos/Story_Title_with_subtitles.mp4` - Final video with subtitles (if enabled)
- `videos/Story_Title_hashtags.txt` - Generated hashtags for social media

Notes: 
- Video titles start with the Reddit post title, followed by the story content
- Intermediate audio files are automatically cleaned up after processing

## API Requirements 🔑

### Required APIs

**ElevenLabs** (Required)
- Sign up at [elevenlabs.io](https://elevenlabs.io)
- Get API key from dashboard
- Free tier includes 10k characters/month

### Optional APIs

**OpenAI** (Recommended)
- Sign up at [platform.openai.com](https://platform.openai.com)
- Create API key
- Improves text processing quality

**ZapCap** (For Subtitles)
- Sign up at [zapcap.ai](https://zapcap.ai)
- Get API key
- $0.10 per minute of video processed
- Long videos (5+ minutes) automatically split into 3-minute chunks for faster processing
- Processing timeout automatically adjusts based on video length


## Troubleshooting 🛠️

### Common Issues

**"ModuleNotFoundError"**
- Run `pip install -r requirements.txt`

**"API key not found"**
- Check your `.env` file
- Ensure API keys are valid

**"Background video not found"**
- Place `background_video.mp4` in project directory
- Check file name and format

**"Rate limited"**
- Reddit: Add delays between requests
- ElevenLabs: Check your usage limits
- OpenAI: Monitor rate limits

### Video Issues

**Video too long**
- Reddit posts are not summarized to preserve content
- Long videos (5+ minutes) automatically split into chunks for subtitle processing
- Each 3-minute chunk processes much faster than a single long video
- Consider shorter posts for fastest processing

**Audio/video sync issues**
- MoviePy handles synchronization automatically
- Check background video format and codec

## Limitations ⚠️

- Long posts create very long videos (no summarization)
- Reddit rate limiting may require delays
- Subtitle generation costs $0.10/minute with ZapCap
- Videos over 5 minutes automatically use chunked processing for reliability

## Tips for Best Results 💡

1. Choose engaging Reddit posts with good storytelling
2. Use high-quality background videos that loop well
3. Test with shorter posts first
4. Monitor API usage limits

## Legal Notes 📝

- Respect Reddit's terms of service
- Give credit to original Reddit authors
- Ensure you have rights to background video content

## Support 🆘

If you encounter issues:
1. Check the troubleshooting section
2. Verify all API keys are valid
3. Test individual components
4. Check file permissions and paths

---

**Ready to create engaging videos from Reddit stories? Let's go! 🎬✨**
