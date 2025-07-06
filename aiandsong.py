import os
import requests
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import db_manager

app = Flask(__name__)
app.secret_key = 'your_super_secret_key'
CORS(app)

# --- Groq API ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# --- Emoji Map ---
EMOJI_MAP = {
    "happy": "😄", "sad": "😢", "angry": "😡", "cool": "😎", "sleepy": "😴", "shocked": "😲", "crying": "😭", "neutral": "😐",
    "blessed": "🙏", "mind blown": "🧠", "lazy": "🚪", "low": "🥺", "lovely": "😍", "tired": "🥱", "stressed": "😰",
    "excited": "🤩", "loved": "❤️", "relaxed": "😌", "motivated": "🔥", "bored": "😒", "anxious": "😬", "confused": "😕"
}

# --- Mood Tips ---
MOOD_TIPS = {
    "happy": "Keep spreading your joy. Try sharing it with a friend!",
    "sad": "It’s okay to feel sad. Take time to rest and recharge.",
    "angry": "Take a deep breath. A quick walk might help.",
    "excited": "Channel your energy into something fun or creative!",
    "tired": "Prioritize rest. Tomorrow is another chance.",
    "bored": "Try a new hobby or explore something random!",
    "anxious": "Take deep breaths. You’ve got this.",
    "confused": "It’s okay not to have all the answers. Clarity will come.",
    "relaxed": "Peace of mind is priceless. Keep enjoying it.",
    "motivated": "Use your momentum to tackle goals!",
    "loved": "Let someone know they’re special today!",
    "neutral": "Try doing something you enjoy to spark joy."
}

# --- Song Library ---
SONG_LIBRARY = {
    "happy": ["Happy - Pharrell Williams", "Phir Se Ud Chala - Rockstar"],
    "sad": ["Channa Mereya - ADHM", "Someone Like You - Adele"],
    "excited": ["Apna Time Aayega", "Can't Stop The Feeling!"],
    "relaxed": ["Ilahi - YJHD", "Let Her Go - Passenger"],
    "angry": ["Zinda - Bhaag Milkha Bhaag", "Stronger - Kanye West"],
    "neutral": ["Kesariya - Brahmastra", "Let It Be - Beatles"],
    "loved": ["Raabta", "Perfect - Ed Sheeran"],
    "motivated": ["Lakshya Title", "Believer - Imagine Dragons"],
    "bored": ["Dance Monkey", "Tunak Tunak Tun"],
    "anxious": ["Let It Go", "Fix You - Coldplay"],
    "tired": ["Khaabon Ke Parinday", "Say You Won’t Let Go"],
    "confused": ["Mad World", "Clocks - Coldplay"]
}

# --- Spotify Playlist Embed URLs ---
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

# --- AI Detection via Groq ---
def detect_user_mood_and_suggestions(text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    system_prompt = """
    You are an emotional support assistant. Given the user's text, detect their mood from:
    ["happy", "sad", "angry", "excited", "tired", "anxious", "confused", "relaxed", "bored", "neutral", "motivated", "loved"].
    Reply in JSON with keys: mood, emoji, suggestions (list of 3 ideas).
    Example:
    {"mood": "sad", "emoji": "😢", "suggestions": ["Go for a walk", "Talk to a friend", "Listen to calming music"]}
    """
    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        "max_tokens": 300,
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        content = response.json()["choices"][0]["message"]["content"]
        result = eval(content)  # Use json.loads if well-formatted JSON
        return result["mood"], result["emoji"], result["suggestions"]
    except Exception as e:
        print("Groq Error:", e)
        return "neutral", "😐", ["Try deep breathing", "Take a walk", "Journal your thoughts"]

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

@app.route('/detect_mood', methods=["POST"])
def detect_mood():
    text = request.form.get('text', '').strip()
    if not text:
        return render_template("index1.html", error="Please describe your mood.")
    mood, emoji, suggestions = detect_user_mood_and_suggestions(text)
    session['text'] = text
    session['mood'] = mood
    session['emoji'] = emoji
    session['suggestions'] = suggestions
    return redirect(url_for('mood_detail'))

@app.route('/mood_details')
def mood_detail():
    mood = session.get("mood", "neutral")
    emoji = session.get("emoji", "😐")
    text = session.get("text", "")
    suggestions = session.get("suggestions", [])
    tip = MOOD_TIPS.get(mood, "You're doing your best.")
    playlist_url = generate_spotify_url(mood)
    playlist_songs = SONG_LIBRARY.get(mood, [])
    return render_template("mood_details.html", mood_name=mood, mood_emoji=emoji,
                           tip=tip, suggestion=suggestions, playlist_url=playlist_url,
                           playlist_songs=playlist_songs)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    db_manager.init_db()
    app.run(debug=True)
