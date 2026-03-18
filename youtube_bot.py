"""
YouTube Kids Cartoon Story Automation Bot
==========================================
Automatically creates and uploads kids cartoon story videos
using 100% FREE AI APIs - runs daily via GitHub Actions

APIs Used:
- Gemini API (Free) - Story generation
- Pollinations.ai (100% Free, no signup) - Image generation
- Hugging Face (Free tier) - Backup image generation
- ElevenLabs (Free tier) - English voice
- gTTS (Completely Free) - Hindi voice
- MoviePy (Free library) - Video creation
- YouTube Data API v3 - Upload video

Required GitHub Secrets:
- GEMINI_API_KEY
- ELEVENLABS_API_KEY
- YOUTUBE_CLIENT_SECRET (OAuth JSON content)
"""

import os
import sys
import json
import time
import random
import requests
import textwrap
from pathlib import Path
from datetime import datetime

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────

GEMINI_API_KEY      = os.environ.get("GEMINI_API_KEY", "")
ELEVENLABS_API_KEY  = os.environ.get("ELEVENLABS_API_KEY", "")
CLIENT_SECRET_JSON  = os.environ.get("YOUTUBE_CLIENT_SECRET", "")

# Video settings
VIDEO_WIDTH         = 1280
VIDEO_HEIGHT        = 720
FPS                 = 24
OUTPUT_DIR          = "output"

# Language: randomly pick English or Hindi each day
LANGUAGE = random.choice(["english", "hindi"])

# ─── STORY TOPICS ──────────────────────────────────────────────────────────────

STORY_TOPICS = [
    "a brave little lion who learns to share",
    "a tiny elephant who discovers a magical forest",
    "a curious bunny who finds a hidden treasure",
    "a friendly dragon who helps lost animals",
    "a small turtle who wins a race with kindness",
    "a baby owl who is afraid of the dark",
    "a clever fox who outsmarts a greedy wolf",
    "a rainbow butterfly who saves her garden friends",
    "a young bear who learns the value of honesty",
    "a magical fish who grants three wishes",
    "a little star who falls from the sky",
    "a funny monkey who learns not to be selfish",
    "a kind giraffe who helps shorter animals",
    "a brave mouse who saves the jungle",
    "a lost penguin who finds his way home",
]

# ─── STEP 1: GENERATE STORY ────────────────────────────────────────────────────

def generate_story():
    """Generate a kids cartoon story using Gemini API"""
    print("\n📖 Generating story with Gemini AI...")

    topic = random.choice(STORY_TOPICS)

    if LANGUAGE == "hindi":
        prompt = f"""
        एक छोटे बच्चों की कहानी लिखो {topic} के बारे में।
        कहानी में 5 दृश्य (scenes) होने चाहिए।
        प्रत्येक दृश्य 2-3 वाक्यों का हो।
        कहानी सरल, मजेदार और नैतिक शिक्षा वाली हो।

        JSON format में जवाब दो:
        {{
            "title": "कहानी का शीर्षक",
            "moral": "नैतिक शिक्षा",
            "scenes": [
                {{"scene_number": 1, "text": "दृश्य पाठ", "image_prompt": "cartoon scene in english"}},
                {{"scene_number": 2, "text": "दृश्य पाठ", "image_prompt": "cartoon scene in english"}},
                {{"scene_number": 3, "text": "दृश्य पाठ", "image_prompt": "cartoon scene in english"}},
                {{"scene_number": 4, "text": "दृश्य पाठ", "image_prompt": "cartoon scene in english"}},
                {{"scene_number": 5, "text": "दृश्य पाठ", "image_prompt": "cartoon scene in english"}}
            ]
        }}
        Only respond with JSON, no extra text.
        """
    else:
        prompt = f"""
        Write a short kids cartoon story about {topic}.
        Exactly 5 scenes, each 2-3 simple sentences for young children.
        Fun, engaging, with a positive moral lesson.

        Reply ONLY with this JSON, no extra text:
        {{
            "title": "Story Title",
            "moral": "The moral of the story",
            "scenes": [
                {{"scene_number": 1, "text": "Scene text", "image_prompt": "cute cartoon illustration, colorful, kids style"}},
                {{"scene_number": 2, "text": "Scene text", "image_prompt": "cute cartoon illustration, colorful, kids style"}},
                {{"scene_number": 3, "text": "Scene text", "image_prompt": "cute cartoon illustration, colorful, kids style"}},
                {{"scene_number": 4, "text": "Scene text", "image_prompt": "cute cartoon illustration, colorful, kids style"}},
                {{"scene_number": 5, "text": "Scene text", "image_prompt": "cute cartoon illustration, colorful, kids style"}}
            ]
        }}
        """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 1500}
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    story = json.loads(raw_text)
    print(f"✅ Story generated: {story['title']}")
    return story


# ─── STEP 2: GENERATE IMAGES (100% FREE) ───────────────────────────────────────

def generate_image_pollinations(prompt, scene_num):
    """
    Generate image using Pollinations.ai
    100% FREE - No API key - No signup - Unlimited
    """
    print(f"🎨 Generating image {scene_num} with Pollinations.ai...")

    full_prompt = f"{prompt}, cute cartoon style, bright vivid colors, kids friendly, Disney Pixar style, no text"
    encoded_prompt = requests.utils.quote(full_prompt)

    # Add random seed so each run gets different image
    seed = random.randint(1, 99999)
    image_url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={VIDEO_WIDTH}&height={VIDEO_HEIGHT}&nologo=true&seed={seed}"
    )

    img_path = f"{OUTPUT_DIR}/scene_{scene_num}.jpg"
    response = requests.get(image_url, timeout=90)
    with open(img_path, "wb") as f:
        f.write(response.content)

    print(f"✅ Image {scene_num} saved!")
    return img_path


def generate_image_huggingface(prompt, scene_num):
    """
    Backup: Generate image using Hugging Face free API
    Uses Stable Diffusion XL - Free tier
    """
    print(f"🎨 Generating image {scene_num} with Hugging Face...")

    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Content-Type": "application/json"}

    full_prompt = f"{prompt}, cute cartoon style, bright colors, kids friendly, Pixar style"
    response = requests.post(
        API_URL,
        headers=headers,
        json={"inputs": full_prompt},
        timeout=60
    )

    img_path = f"{OUTPUT_DIR}/scene_{scene_num}.jpg"
    with open(img_path, "wb") as f:
        f.write(response.content)

    print(f"✅ Image {scene_num} saved!")
    return img_path


def generate_images(scenes):
    """Generate images for all scenes using free APIs"""
    image_paths = []

    for scene in scenes:
        scene_num = scene["scene_number"]
        prompt = scene["image_prompt"]

        try:
            # Primary: Pollinations.ai (100% free)
            img_path = generate_image_pollinations(prompt, scene_num)
        except Exception as e:
            print(f"⚠️ Pollinations failed: {e}. Trying Hugging Face...")
            try:
                img_path = generate_image_huggingface(prompt, scene_num)
            except Exception as e2:
                print(f"⚠️ Hugging Face failed too: {e2}")
                # Create blank colored image as last resort
                from PIL import Image, ImageDraw
                colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"]
                img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), colors[scene_num % len(colors)])
                img_path = f"{OUTPUT_DIR}/scene_{scene_num}.jpg"
                img.save(img_path)

        image_paths.append(img_path)
        time.sleep(3)  # Small delay between requests

    return image_paths


# ─── STEP 3: GENERATE VOICE ────────────────────────────────────────────────────

def generate_voice_elevenlabs(text, scene_num):
    """Generate English voice using ElevenLabs free tier"""
    print(f"🎙️ Generating English voice for scene {scene_num}...")

    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.75, "similarity_boost": 0.75}
    }

    response = requests.post(url, headers=headers, json=data)
    audio_path = f"{OUTPUT_DIR}/voice_{scene_num}.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)

    print(f"✅ Voice {scene_num} saved!")
    return audio_path


def generate_voice_gtts(text, scene_num, lang="en"):
    """Generate voice using gTTS - 100% FREE"""
    from gtts import gTTS
    print(f"🎙️ Generating {'Hindi' if lang=='hi' else 'English'} voice for scene {scene_num}...")

    tts = gTTS(text=text, lang=lang, slow=False)
    audio_path = f"{OUTPUT_DIR}/voice_{scene_num}.mp3"
    tts.save(audio_path)

    print(f"✅ Voice {scene_num} saved!")
    return audio_path


def generate_voices(scenes):
    """Generate voice for all scenes"""
    audio_paths = []

    for scene in scenes:
        scene_num = scene["scene_number"]
        text = scene["text"]

        if LANGUAGE == "hindi":
            # gTTS for Hindi - completely free
            audio_path = generate_voice_gtts(text, scene_num, lang="hi")
        else:
            # Try ElevenLabs for English, fall back to gTTS
            try:
                if ELEVENLABS_API_KEY:
                    audio_path = generate_voice_elevenlabs(text, scene_num)
                else:
                    audio_path = generate_voice_gtts(text, scene_num, lang="en")
            except Exception as e:
                print(f"⚠️ ElevenLabs failed: {e}. Using gTTS...")
                audio_path = generate_voice_gtts(text, scene_num, lang="en")

        audio_paths.append(audio_path)

    return audio_paths


# ─── STEP 4: CREATE VIDEO ──────────────────────────────────────────────────────

def create_video(story, image_paths, audio_paths):
    """Combine images + audio into final MP4 video"""
    from moviepy.editor import (
        ImageClip, AudioFileClip, TextClip,
        CompositeVideoClip, concatenate_videoclips
    )

    print("\n🎬 Creating video...")
    clips = []

    # Title card
    title_clip = TextClip(
        story["title"],
        fontsize=65,
        color="yellow",
        bg_color="#1a1a2e",
        font="Liberation-Sans-Bold",
        size=(VIDEO_WIDTH, VIDEO_HEIGHT),
        method="caption"
    ).set_duration(3)
    clips.append(title_clip)

    # Scene clips
    for i, (img_path, audio_path, scene) in enumerate(
        zip(image_paths, audio_paths, story["scenes"])
    ):
        audio = AudioFileClip(audio_path)
        duration = audio.duration + 1.0

        img_clip = (ImageClip(img_path)
                    .set_duration(duration)
                    .resize((VIDEO_WIDTH, VIDEO_HEIGHT)))

        subtitle = (TextClip(
            textwrap.fill(scene["text"], width=55),
            fontsize=38,
            color="white",
            bg_color="rgba(0,0,0,0.65)",
            font="Liberation-Sans-Bold",
            method="caption",
            size=(VIDEO_WIDTH - 80, None)
        )
        .set_position(("center", VIDEO_HEIGHT - 180))
        .set_duration(duration))

        scene_clip = CompositeVideoClip([img_clip, subtitle]).set_audio(audio)
        clips.append(scene_clip)

    # Moral card at end
    moral_clip = TextClip(
        f"🌟 Moral of the Story 🌟\n\n{story['moral']}",
        fontsize=50,
        color="white",
        bg_color="#2d6a4f",
        font="Liberation-Sans-Bold",
        size=(VIDEO_WIDTH, VIDEO_HEIGHT),
        method="caption"
    ).set_duration(5)
    clips.append(moral_clip)

    # Combine all
    final_video = concatenate_videoclips(clips, method="compose")
    output_path = f"{OUTPUT_DIR}/final_video.mp4"
    final_video.write_videofile(
        output_path, fps=FPS,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )

    print(f"✅ Video created: {output_path}")
    return output_path


# ─── STEP 5: UPLOAD TO YOUTUBE ─────────────────────────────────────────────────

def upload_to_youtube(video_path, story):
    """Upload video to YouTube"""
    import pickle
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.auth.transport.requests import Request

    print("\n📤 Uploading to YouTube...")

    client_secret_path = "client_secret.json"
    with open(client_secret_path, "w") as f:
        f.write(CLIENT_SECRET_JSON)

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    youtube = build("youtube", "v3", credentials=creds)

    lang_tag = "Hindi" if LANGUAGE == "hindi" else "English"
    tags = ["kids story", "cartoon", "bedtime story", "moral story",
            "kids animation", "children", "educational", lang_tag.lower()]

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": f"{story['title']} | Kids Cartoon Story | {lang_tag}",
                "description": (
                    f"🌟 {story['title']} 🌟\n\n"
                    f"Moral: {story['moral']}\n\n"
                    f"A fun and educational cartoon story for kids!\n\n"
                    f"#{' #'.join(tags)}"
                ),
                "tags": tags,
                "categoryId": "1",
                "defaultLanguage": "hi" if LANGUAGE == "hindi" else "en",
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": True,
            }
        },
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )

    response = request.execute()
    video_id = response["id"]
    print(f"✅ Uploaded! https://youtube.com/watch?v={video_id}")
    return video_id


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("🎬 YouTube Kids Story Bot Starting...")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🌐 Language: {LANGUAGE.upper()}")
    print("🆓 Using: Pollinations.ai + gTTS (100% Free!)")
    print("=" * 60)

    Path(OUTPUT_DIR).mkdir(exist_ok=True)

    story      = generate_story()
    img_paths  = generate_images(story["scenes"])
    aud_paths  = generate_voices(story["scenes"])
    video_path = create_video(story, img_paths, aud_paths)
    upload_to_youtube(video_path, story)

    print("\n🎉 Done! Video uploaded successfully!")


if __name__ == "__main__":
    main()