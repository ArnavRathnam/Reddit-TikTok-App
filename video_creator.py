import os
import requests
from moviepy.editor import *
from reddit_tiktok_converter import *
import re

# === CONFIGURATION ===
ELEVENLABS_API_KEY = "sk_7898700bca0597d6f287a64a43940058c8853e8ee2b710c0"
VOICE_ID = "alFofuDn3cOwyoz1i44T"  # Get this from ElevenLabs dashboard
BACKGROUND_VIDEO = "background.mp4"  # Or use a static image with ImageClip
OUTPUT_VIDEO = "tiktok_output.mp4"

# === STEP 1: TEXT TO SPEECH ===
def generate_tts_audio(script_lines, output_path="voiceover.mp3"):
    text = " ".join(script_lines)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"TTS generation failed: {response.text}")

    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path

# === STEP 2: BUILD VIDEO ===
def build_video(script_lines, audio_path, background_path, output_path):
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration

    # Load background (loop if needed)
    if background_path.endswith(".mp4"):
        video = VideoFileClip(background_path)
        if video.duration < duration:
            n_loops = int(duration // video.duration) + 1
            video = concatenate_videoclips([video] * n_loops)
        video = video.subclip(0, duration).resize((1080, 1920))
    else:
        video = ImageClip(background_path, duration=duration).resize((1080, 1920))

    # Create subtitles
    lines = script_lines
    words_per_line = [len(l.split()) for l in lines]
    total_words = sum(words_per_line)
    word_rate = duration / total_words

    subtitle_clips = []
    start = 0
    for line in lines:
        line_words = len(line.split())
        end = start + line_words * word_rate
        txt_clip = TextClip(line, fontsize=80, color='white', method='caption', size=(900, None))
        txt_clip = txt_clip.set_position(('center', 'center')).set_duration(end - start).set_start(start)
        subtitle_clips.append(txt_clip)
        start = end

    final = CompositeVideoClip([video] + subtitle_clips)
    final = final.set_audio(audio_clip)
    final.write_videofile(output_path, fps=30)

# === MAIN PIPELINE ===
def main():
    # Automatically fetch and process a Reddit post
    url = input("Enter Reddit post JSON URL: ").strip()
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch data: HTTP {response.status_code}")
        return

    data = response.json()
    post_data = data[0]['data']['children'][0]['data']
    title = post_data['title']
    content_raw = post_data['selftext']
    content = clean_content(content_raw)

    user_match = re.search(r'OOP is u/(\w+)', content)
    sub_match = re.search(r'in r/(\w+)', content)
    username = user_match.group(1) if user_match else 'unknown_user'
    origin_subreddit = sub_match.group(1) if sub_match else 'unknown_sub'

    dates = extract_dates(content)
    rel_times = calculate_relative_times(dates)

    # Create script as subtitle lines
    script_lines = []
    script_lines.append(title)
    script_lines.append(f"Originally posted by u/{username} in r/{origin_subreddit}")
    update_map = {label: tag for tag, label in rel_times}
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        for tag, label in rel_times:
            if label.lower() in line.lower():
                script_lines.append(tag)
                break
        else:
            script_lines.extend(split_line_for_subtitles(line))

    # TTS + Video
    audio_path = generate_tts_audio(script_lines)
    build_video(script_lines, audio_path, BACKGROUND_VIDEO, OUTPUT_VIDEO)

def split_line_for_subtitles(line, max_words=10):
    words = line.strip().split()
    return [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

if __name__ == "__main__":
    main()
