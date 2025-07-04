import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from spotipy.oauth2 import SpotifyOAuth
import db_manager
from db_manager import init_db
# from transformers import AutoTokenizer, AutoModelForSequenceClassification # Removed if not directly used
# import torch # Removed if not directly used
import json
import numpy as np


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_super_secret_key') # Use environment variable for secret key
CORS(app)

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-read-private user-read-email" # Added a basic scope for Spotify integration
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
        response.raise_for_status() # Raise an exception for HTTP errors
        content = response.json()["choices"][0]["message"]["content"].strip()
        result = json.loads(content)
        return result["mood"], result["emoji"], result["suggestions"]
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return "neutral", "😐", ["Could not connect to AI service.", "Please try again later."]
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}. Response content: {content}")
        return "neutral", "😐", ["Could not process AI response.", "Please try again later."]
    except KeyError as e:
        print(f"Key Error: {e}. Unexpected AI response format.")
        return "neutral", "😐", ["Unexpected AI response format.", "Please try again later."]
    except Exception as e:
        print(f"An unexpected error occurred in get_ai_suggestion: {e}")
        return "neutral", "😐", ["An unexpected error occurred.", "Please try again."]


# --- Spotify Embed Link Generator ---
def generate_spotify_url(mood):
    playlist_links = {
    "happy": "https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGoYBM5M?utm_source=generator", # Happy Hits!
    "sad": "https://open.spotify.com/embed/playlist/37i9dQZF1DXa2SPUyWl8Y", # Life Sucks
    "angry": "https://open.spotify.com/embed/playlist/37i9dQZF1DXdgnR6m9Sytm", # Rock Hard
    "relaxed": "https://open.spotify.com/embed/playlist/37i9dQZF1DXeeL10wUf7JJ", # Chill Hits
    "excited": "https://open.spotify.com/embed/playlist/37i9dQZF1DX0Bxgyx9q1P", # Hype
    "tired": "https://open.spotify.com/embed/playlist/37i9dQZF1DX4wT3Gw5JgE8", # Sleep
    "bored": "https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGoYBM5M", # Happy (fallback for boredom, or find a specific one)
    "confused": "https://open.spotify.com/embed/playlist/37i9dQZF1DWVch4Y74F62L", # Deep Focus
    "anxious": "https://open.spotify.com/embed/playlist/37i9dQZF1DX4sWPMzJ3A5X", # Calm Vibes
    "neutral": "https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGoYBM5M", # Lofi Beats (or a general chill playlist)
    "motivated": "https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGoYBM5M", # Motivation Mix
    "loved": "https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGoYBM5M" # Love Songs
}
    # Using open.spotify.com/embed/playlist/... for direct embedding
    return playlist_links.get(mood, playlist_links["neutral"])

# --- Routes ---
@app.route('/')
def land():
    return render_template('land.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        age = request.form.get('age')
        gender = request.form.get('gender')

        # IMPORTANT: This is a dummy login for demonstration.
        # In a real application, you MUST implement proper user registration,
        # password hashing (e.g., using generate_password_hash and check_password_hash),
        # and retrieve a unique user_id from a database after successful authentication.
        # For now, we'll assign a simple incremental ID for demonstration purposes
        # to simulate different users.
        if username:
            # For demonstration, let's assign a simple user_id based on username length
            # In a real app, this would be from your user database.
            session['user_id'] = len(username) # This is just for demo, not secure or unique enough
            session['username'] = username
            session['email'] = email
            session['age'] = age
            session['gender'] = gender
            return redirect(url_for('dashboard'))
        else:
            error = "Username is required to login."
            return render_template('auth.html', error=error)

    return render_template('auth.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user_id = session['user_id']
    # Pass user_id to get_all_moods to retrieve only the current user's moods
    moods = db_manager.get_all_moods(current_user_id)
    return render_template('dashboard.html', moods=moods)

@app.route('/index1')
def index1():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index1.html')

@app.route('/detect_mood', methods=["POST"])
def detect_mood():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    text = request.form.get('text', '').strip()
    if not text:
        return render_template("index1.html", error="Please describe your mood.")
    
    mood, emoji, suggestions = get_ai_suggestion(text)
    session['text'] = text
    session['mood'] = mood
    session['emoji'] = emoji
    session['suggestions'] = suggestions
    return redirect(url_for('mood_detail'))

@app.route('/mood_details')
def mood_detail():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    text = session.get("text", "I'm feeling...")
    mood = session.get("mood", "neutral")
    emoji = session.get("emoji", "😐")
    suggestions = session.get("suggestions", [])
    tip = MOOD_TIPS.get(mood, "You're doing your best.")
    playlist_url = generate_spotify_url(mood)
    playlist_songs = SONG_LIBRARY.get(mood, []) # Note: SONG_LIBRARY might not align perfectly with Spotify playlists
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
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.get_json()
    emoji = data.get('emoji')
    name = data.get('name')
    reason = data.get('reason')
    timestamp = data.get('timestamp')
    if not all([emoji, name, timestamp]):
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400
    try:
        current_user_id = session['user_id']
        db_manager.add_mood(current_user_id, emoji, name, reason, timestamp)
        return jsonify({'status': 'success', 'message': 'Mood added successfully!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_moods')
def get_moods():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    try:
        current_user_id = session['user_id']
        # Pass user_id to get_all_moods to retrieve only the current user's moods
        moods_list = db_manager.get_all_moods(current_user_id)
        return jsonify({'moods': moods_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_mood/<int:mood_id>')
def get_mood(mood_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    current_user_id = session['user_id']
    # Pass user_id to get_mood_by_id to ensure the mood belongs to the user
    mood = db_manager.get_mood_by_id(mood_id, current_user_id)
    if mood:
        return jsonify(status='success', mood=mood)
    return jsonify(status='fail', message='Mood not found or not authorized')

@app.route('/delete_mood/<int:mood_id>', methods=['DELETE'])
def delete_mood_route(mood_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    current_user_id = session['user_id']
    # Pass user_id to delete_mood to ensure the mood belongs to the user
    success = db_manager.delete_mood(mood_id, current_user_id)
    return jsonify(status='success' if success else 'fail')

@app.route('/edit_mood/<int:mood_id>', methods=['PUT'])
def edit_mood(mood_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.get_json()
    current_user_id = session['user_id']
    # Pass user_id to edit_mood to ensure the mood belongs to the user
    success = db_manager.edit_mood(mood_id, current_user_id, data['name'], data['emoji'], data['reason'])
    return jsonify(status='success' if success else 'fail')

if __name__ == "__main__":
    db_manager.init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
