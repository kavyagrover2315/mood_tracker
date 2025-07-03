// Mood-to-Emoji map
const moodEmojiMap = {
  "Happy": "😊",
  "Surprised": "😲",
  "Angry": "😡",
  "Sleepy": "😴",
  "Excited": "🤩",
  "In Love": "😍",
  "Cool": "😎",
  "Neutral": "😐",
  "Cry": "😭"
};

// Mood Quotes
const moodQuotes = {
  "Happy": "Happiness is not something ready-made. It comes from your own actions.",
  "Sad": "The sad soul is a kingdom in itself.",
  "Neutral": "Sometimes, the most profound peace lies in being still.",
  "In Love": "Where there is love, there is life.",
  "Cool": "Stay cool and let the good vibes flow.",
  "Sleepy": "A tired body is not a weakness — it's a sign you’ve given your all.",
  "Angry": "Anger is an acid that can do more harm to the vessel than to anything on which it is poured.",
  "Cry": "Tears are words the heart can't express.",
  "Surprised": "Life's surprises keep us on our toes and our hearts alive.",
  "Excited": "Let your excitement ignite the world around you."
};

// On Load
document.addEventListener('DOMContentLoaded', () => {
  fetchMoods();
  setupEmojiSelection();
  setupBubbleBackground();
  positionEmojisInCircle();
});

// Emoji Circle
function positionEmojisInCircle() {
  const emojis = document.querySelectorAll('.emoji-item');
  const radius = 100;
  const centerX = 125;
  const centerY = 125;
  const total = emojis.length;

  emojis.forEach((emoji, index) => {
    const angle = (index / total) * (2 * Math.PI);
    const x = centerX + radius * Math.cos(angle) - 25;
    const y = centerY + radius * Math.sin(angle) - 25;
    emoji.style.left = `${x}px`;
    emoji.style.top = `${y}px`;
  });
}

function setupEmojiSelection() {
  const emojis = document.querySelectorAll('.emoji-item');
  const emojiName = document.getElementById('emojiName');
  const moodLabel = document.getElementById('selectedMoodLabel');

  emojis.forEach(emoji => {
    emoji.addEventListener('click', () => {
      emojis.forEach(e => e.classList.remove('selected'));
      emoji.classList.add('selected');
      const name = emoji.getAttribute('data-name');
      emojiName.textContent = name;
      moodLabel.textContent = `Selected Mood: ${name}`;
    });
  });
}

function openPopup() {
  const popup = document.getElementById('popup');
  popup.style.display = 'flex';
  document.getElementById('emojiName').textContent = 'Neutral';
  document.getElementById('selectedMoodLabel').textContent = 'Selected Mood: Neutral';
  document.getElementById('reasonInput').value = '';
  popup.removeAttribute('data-edit-id');
}

document.getElementById('popup').addEventListener('click', function (event) {
  if (event.target === this) this.style.display = 'none';
});

document.getElementById('submitMoodBtn').addEventListener('click', () => {
  const moodName = document.getElementById('selectedMoodLabel').textContent.replace("Selected Mood: ", "").trim();
  const moodEmoji = moodEmojiMap[moodName] || "😐";
  const reason = document.getElementById('reasonInput').value.trim();

  const payload = {
    name: moodName,
    emoji: moodEmoji,
    reason: reason,
    timestamp: new Date().toISOString()
  };

  fetch('/add_mood', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        document.getElementById('popup').style.display = 'none';
        fetchMoods();
      } else {
        alert('Error saving mood.');
      }
    });
});

function fetchMoods() {
  fetch('/get_moods')
    .then(res => res.json())
    .then(data => {
      renderTimeline(data.moods);
      renderWeekCalendar(data.moods);
    });
}

function renderTimeline(moods) {
  const container = document.getElementById('moodTimeline');
  container.innerHTML = '';
  if (moods.length === 0) {
    container.innerHTML = "<p style='text-align:center'>No moods yet.</p>";
    return;
  }

  moods.forEach(mood => {
    const entryDiv = document.createElement('div');
    entryDiv.classList.add('entry');

    const date = new Date(mood.timestamp);
    const formattedDate = date.toLocaleString('en-US', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
      hour: '2-digit', minute: '2-digit', hour12: true,
      timeZone: 'Asia/Kolkata'
    });

    const quote = moodQuotes[mood.name] || "Embrace your feelings.";
    entryDiv.innerHTML = `
      <h3>${mood.emoji} ${mood.name}</h3>
      <p class="timestamp">${formattedDate}</p>
      <p class="reason">${mood.reason || 'No reason provided.'}</p>
      <p class="quote" style="font-style: italic; color: #555;">${quote}</p>
      <div class="entry-actions">
        <a href="#" onclick="editMood(${mood.id})">Edit</a>
        <a href="#" onclick="deleteMood(${mood.id})">Delete</a>
      </div>
    `;
    container.appendChild(entryDiv);
  });
}

function renderWeekCalendar(moods) {
  const calendar = document.getElementById('weekCalendar');
  calendar.innerHTML = '';
  const today = new Date();
  const weekStart = new Date(today);
  weekStart.setDate(today.getDate() - today.getDay());

  for (let i = 0; i < 7; i++) {
    const day = new Date(weekStart);
    day.setDate(weekStart.getDate() + i);
    const dateStr = day.toISOString().split('T')[0];
    const dayMoods = moods.filter(m => m.timestamp.startsWith(dateStr));
    const moodEmoji = dayMoods.length > 0 ? dayMoods[0].emoji : "";

    const box = document.createElement('div');
    box.classList.add('day-box');
    if (day.toDateString() === today.toDateString()) box.classList.add('active');

    box.innerHTML = `
      <div class="day-name">${day.toLocaleDateString('en-US', { weekday: 'short' })}</div>
      <div class="day-date">${day.getDate()}</div>
      <div class="day-emoji">${moodEmoji}</div>
    `;
    calendar.appendChild(box);
  }
}

function editMood(id) {
  const newName = prompt("Enter new mood name:");
  const newEmoji = prompt("Enter new emoji:");
  const newReason = prompt("Enter new reason:");

  fetch(`/edit_mood/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: newName, emoji: newEmoji, reason: newReason })
  })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') fetchMoods();
    });
}

function deleteMood(id) {
  if (confirm("Are you sure to delete this mood?")) {
    fetch(`/delete_mood/${id}`, { method: 'DELETE' })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') fetchMoods();
      });
  }
}

function setupBubbleBackground() {
  for (let i = 0; i < 30; i++) createBubble();
  setInterval(createBubble, 500);
}

function createBubble() {
  const area = document.querySelector('.background-animation');
  const bubble = document.createElement('span');
  bubble.classList.add('bubble');
  bubble.textContent = ['😊', '🌈', '💜', '✨'][Math.floor(Math.random() * 4)];
  const size = Math.random() * 30 + 20;
  bubble.style.width = `${size}px`;
  bubble.style.height = `${size}px`;
  bubble.style.left = `${Math.random() * 100}vw`;
  bubble.style.animationDuration = `${Math.random() * 20 + 10}s`;
  bubble.style.fontSize = `${size * 0.6}px`;
  area.appendChild(bubble);
  bubble.addEventListener('animationend', () => bubble.remove());
}
