import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from spotipy.oauth2 import SpotifyOAuth
import db_manager
from db_manager import init_db  
from flask import session 
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import json
import numpy as np


app = Flask(__name__)
app.secret_key = 'your_super_secret_key'
CORS(app)

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    
)


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Mood Tips ---
MOOD_TIPS = {
    "happy": "Keep spreading your joy. Try sharing it with a friend!",
    "sad": "It’s okay to feel sad. Take time to rest and recharge.",
    "angry": "Take a deep breath. A quick walk might help.",
    "cool": "Enjoy your vibe! Keep rocking.",
    "sleepy": "Get some rest or power nap if possible.",
    "shocked": "Take time to process. Write down your thoughts.",
    "crying": "It’s okay to cry. You’re human. Give yourself care.",
    "neutral": "Try doing something you enjoy to spark joy.",
    "blessed": "Gratitude grounds us. Reflect on what you’re thankful for.",
    "mind blown": "Great thoughts! Take notes or talk to someone about it.",
    "lazy": "Do one small task—it’ll help boost your energy.",
    "low": "You are not alone. Reach out if needed.",
    "lovely": "You’re radiating kindness. Pass it on.",
    "tired": "Prioritize rest. Tomorrow is another chance.",
    "stressed": "Pause. Breathe. You’ve handled tough days before.",
    "excited": "Channel your energy into something creative or fun!",
    "loved": "Let someone know they’re special today!",
    "relaxed": "Peace of mind is priceless. Keep enjoying it.",
    "motivated": "Use your momentum to tackle goals!",
    "bored": "Try a new hobby or explore something random!",
    "anxious": "Take deep breaths. You’ve got this.",
    "confused": "It’s okay not to have all the answers. Clarity will come."
}

# --- Mood Categories ---
MOOD_CATEGORIES = {
    "happy": ["happy", "joyful", "grateful", "cheerful", "awesome"],
    "excited": ["excited", "thrilled", "buzzing", "pumped"],
    "loved": ["loved", "romantic", "heart full"],
    "relaxed": ["relaxed", "calm", "chilling", "peaceful"],
    "motivated": ["motivated", "focused", "productive"],
    "neutral": ["neutral", "meh", "okay"],
    "bored": ["bored", "dull", "nothing to do"],
    "anxious": ["anxious", "worried", "nervous"],
    "sad": ["sad", "down", "depressed", "blue"],
    "angry": ["angry", "mad", "pissed", "furious"],
    "tired": ["tired", "exhausted", "burnt out"],
    "confused": ["confused", "uncertain", "don’t understand"],
  

}

# --- Song Library ---
SONG_LIBRARY = {
    "happy": ["Happy - Pharrell Williams", "Phir Se Ud Chala - Rockstar"],
    "sad": ["Channa Mereya - ADHM", "Someone Like You - Adele"],
    "excited": ["Apna Time Aayega - Gully Boy", "Can't Stop The Feeling!"],
    "relaxed": ["Ilahi - YJHD", "Let Her Go - Passenger"],
    "angry": ["Zinda - Bhaag Milkha Bhaag", "Stronger - Kanye West"],
    "neutral": ["Kesariya - Brahmastra", "Let It Be - Beatles"],
    "loved": ["Raabta - Agent Vinod", "Perfect - Ed Sheeran"],
    "motivated": ["Lakshya - Title Track", "Believer - Imagine Dragons"],
    "bored": ["Dance Monkey", "Tunak Tunak Tun"],
    "anxious": ["Let It Go", "Fix You - Coldplay"],
    "tired": ["Khaabon Ke Parinday", "Say You Won’t Let Go"],
    "confused": ["Mad World", "Clocks - Coldplay"]
}

# --- Emoji Mapping ---
EMOJI_MAP = {
    "happy": "😄", "sad": "😢", "angry": "😡", "cool": "😎",
    "sleepy": "😴", "shocked": "😲", "crying": "😭", "neutral": "😐",
    "blessed": "🙏", "mind blown": "🧠", "lazy": "🚪", "low": "🥺",
    "lovely": "😍", "tired": "🥱", "stressed": "😰", "excited": "🤩",
    "loved": "❤️", "relaxed": "😌", "motivated": "🔥", "bored": "😒",
    "anxious": "😬", "confused": "😕"
}

# --- AI Suggestion ---
def get_ai_suggestion(text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = """
You are a supportive emotional wellness assistant.
Your job is to:
1. Detect the user's mood (like happy, sad, anxious, excited, tired, bored, etc.).
2. Suggest five brief and helpful tips, self-care ideas, or advice to support them.
3. Respond ONLY in this JSON format:
{
  "mood": "<one-word-mood>",
  "emoji": "<emoji>",
  "suggestions": [
    "Tip 1",
    "Tip 2",
    "Tip 3",
    "Tip 4",
    "Tip 5"
  ]
}
Do NOT include explanations or extra text.
"""

    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"My message: {text}"}
        ],
        "max_tokens": 300,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        content = response.json()["choices"][0]["message"]["content"].strip()

        result = json.loads(content)
        return result["mood"], result["emoji"], result["suggestions"]

    except Exception as e:
        print("Error:", e)
        return "neutral", "😐", ["Take a deep breath.", "Go for a short walk.", "Write your thoughts down.", "Talk to someone you trust.", "Listen to calming music."]




def generate_spotify_url(mood):
    playlist_links = {
        "happy": "https://open.spotify.com/embed/playlist/37i9dQZF1DXdPec7aLTmlC",
        "sad": "https://open.spotify.com/embed/playlist/37i9dQZF1DX7qK8ma5wgG1",
        "angry": "https://open.spotify.com/embed/playlist/37i9dQZF1DWY6vTWIdZ54A",
        "relaxed": "https://open.spotify.com/embed/playlist/37i9dQZF1DX3rxVfibe1L0",
        "excited": "https://open.spotify.com/embed/playlist/37i9dQZF1DX1tW4VlEfDSS",
        "tired": "https://open.spotify.com/embed/playlist/37i9dQZF1DX1s9knjP51Oa",
        "bored": "https://open.spotify.com/embed/playlist/37i9dQZF1DWYp5sAHdz27Y",
        "confused": "https://open.spotify.com/embed/playlist/37i9dQZF1DWVrtsSlLKzro",
        "anxious": "https://open.spotify.com/embed/playlist/37i9dQZF1DX3YSRoSdA634",
        "neutral": "https://open.spotify.com/embed/playlist/37i9dQZF1DWWMOmoXKqHTD",
        "motivated": "https://open.spotify.com/embed/playlist/37i9dQZF1DWZQaaqNMbbXa",
        "loved": "https://open.spotify.com/embed/playlist/37i9dQZF1DWYxwmBaMqxsl"
    }
    return playlist_links.get(mood, playlist_links["neutral"])
    
@app.before_first_request
def initialize_database():
    init_db()
# --- Routes ---
@app.route('/')
def land():
    return render_template('land.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user_id'] = 1
        return redirect(url_for('dashboard'))
    return render_template('auth.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    moods = db_manager.get_all_moods()
    return render_template('dashboard.html', moods=moods)

@app.route('/index1')
def index1():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index1.html')


@app.route("/")
def home():
    return render_template("index1.html")


@app.route("/detect_mood", methods=["POST"])
def detect_mood():
    text = request.form.get('text', '').strip()

    if not text:
        return render_template("index1.html", error="Please describe your mood.")

    # 🧠 NEW: Use LLaMA to get mood, emoji, and 5 suggestions
    mood, emoji, suggestions = get_ai_suggestion(text)

    # Save to session
    session['text'] = text
    session['mood'] = mood
    session['emoji'] = emoji
    session['suggestions'] = suggestions  # ✔️ Save list of suggestions

    return redirect(url_for('mood_detail'))


@app.route("/mood_details")
def mood_detail():
    text = session.get("text", "I'm feeling...")
    mood = session.get("mood", "neutral")
    emoji = session.get("emoji", "😐")
    suggestions = session.get("suggestions", ["Take a deep breath."])  # ✔️ Get suggestion list

    tip = MOOD_TIPS.get(mood, "You're doing your best.")
    playlist_url = generate_spotify_url(mood)
    playlist_songs = SONG_LIBRARY.get(mood, [])

    return render_template("mood_details.html",
                           mood_name=mood,
                           mood_emoji=emoji,
                           tip=tip,
                           suggestion_list=suggestions,
                           playlist_url=playlist_url,
                           playlist_songs=playlist_songs)








@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/add_mood', methods=['POST'])
def add_mood():
    data = request.get_json()
    emoji = data.get('emoji')
    name = data.get('name')
    reason = data.get('reason')
    timestamp = data.get('timestamp')

    if not all([emoji, name, timestamp]):
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400

    try:
        user_id = session.get('user_id', None)
        db_manager.add_mood(user_id, emoji, name, reason, timestamp)
        return jsonify({'status': 'success', 'message': 'Mood added successfully!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_moods')
def get_moods():
    try:
        moods_list = db_manager.get_all_moods()
        return jsonify({'moods': moods_list})
    except Exception as e:
        print("Error in /get_moods:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/get_mood/<int:mood_id>')
def get_mood(mood_id):
    mood = db_manager.get_mood_by_id(mood_id)
    if mood:
        return jsonify(status='success', mood=mood)
    return jsonify(status='fail', message='Mood not found')

@app.route('/delete_mood/<int:mood_id>', methods=['DELETE'])
def delete_mood_route(mood_id):
    success = db_manager.delete_mood(mood_id)
    return jsonify(status='success' if success else 'fail')

@app.route('/edit_mood/<int:mood_id>', methods=['PUT'])
def edit_mood(mood_id):
    data = request.get_json()
    success = db_manager.edit_mood(mood_id, data['name'], data['emoji'], data['reason'])
    return jsonify(status='success' if success else 'fail')

if __name__ == "__main__":
    db_manager.init_db()
    port = int(os.environ.get("PORT", 5000))  # or 5000 as fallback
    app.run(host="0.0.0.0", port=port)

