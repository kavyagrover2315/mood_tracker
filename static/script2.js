document.addEventListener("DOMContentLoaded", () => {
  const backgroundAnimationContainer = document.querySelector('.background-animation-container');
  let animationInterval;

  const moodMap = {
    happy: { emoji: "😊", floatingEmojis: ["😊", "😄", "✨", "☀️"] },
    sad: { emoji: "😢", floatingEmojis: ["💧", "🌧️", "😟", "💙"] },
    angry: { emoji: "😠", floatingEmojis: ["🔥", "😡", "💥", "💨"] },
    anxious: { emoji: "😰", floatingEmojis: ["💨", "💭", "〰️", "🍃"] },
    tired: { emoji: "😴", floatingEmojis: ["😴", "☕", "🛌", "💤"] },
    excited: { emoji: "🤩", floatingEmojis: ["🥳", "🎉", "✨", "🎶"] },
    neutral: { emoji: "😐", floatingEmojis: ["✨", "⚪", "☁️", "🧘"] }
  };

  function createFloatingElement(type, content = '') {
    const element = document.createElement('div');
    element.classList.add('floating-element', type);

    if (type === 'bubble') {
      const size = Math.random() * 40 + 20;
      element.style.width = `${size}px`;
      element.style.height = `${size}px`;
    } else {
      const fontSize = Math.random() * 2 + 1 + 'em';
      element.style.fontSize = fontSize;
      element.textContent = content;
    }

    const startX = Math.random() * (window.innerWidth - 50);
    element.style.left = `${startX}px`;
    element.style.bottom = `${-50}px`;

    const duration = Math.random() * 8 + 7;
    const delay = Math.random() * 0.5;
    const xDrift = (Math.random() - 0.5) * 200;

    element.style.animationDuration = `${duration}s`;
    element.style.animationDelay = `${delay}s`;
    element.style.setProperty('--x-drift', `${xDrift}px`);

    backgroundAnimationContainer.appendChild(element);

    element.addEventListener('animationend', () => {
      element.remove();
    });
  }

  function startFloatingAnimations(emojisToUse) {
    if (animationInterval) {
      clearInterval(animationInterval);
    }
    backgroundAnimationContainer.innerHTML = ''; // Clear existing elements

    const finalEmojis = Array.isArray(emojisToUse) && emojisToUse.length > 0
                         ? emojisToUse
                         : moodMap.neutral.floatingEmojis;

    animationInterval = setInterval(() => {
      if (Math.random() < 0.6) {
        createFloatingElement('bubble');
      }

      if (Math.random() < 0.2) {
        createFloatingElement('heart', '❤️');
      }

      if (Math.random() < 0.4 && finalEmojis.length > 0) {
        const randomEmoji = finalEmojis[Math.floor(Math.random() * finalEmojis.length)];
        createFloatingElement('emoji', randomEmoji);
      }
    }, 500);
  }

  // --- Logic for index.html (Mood Input Page) ---
  const moodForm = document.getElementById("moodForm");
  const moodDisplayBox = document.querySelector(".mood-display");
  const moodNameEl = document.getElementById("moodName");
  const detectedEmojiEl = document.getElementById("detectedEmoji");
  const clickInstruction = document.querySelector(".click-instruction");

  if (moodForm) { // Only run this code on index.html
    // Initial display on index.html
    const defaultMoodName = "happy"; // Or fetch from Flask context on page load
    const defaultMoodEmoji = moodMap[defaultMoodName].emoji;
    moodNameEl.textContent = capitalize(defaultMoodName);
    detectedEmojiEl.textContent = defaultMoodEmoji;

    // Start initial animations for index page
    startFloatingAnimations(moodMap.happy.floatingEmojis);


    moodForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const userInput = moodForm.querySelector('input[name="text"]').value;

      try {
        const response = await fetch('/detect_mood', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: `text=${encodeURIComponent(userInput)}`
        });
        const data = await response.json();

        const detectedMood = data.detected_mood;
        const moodDetails = data.mood_details;

        moodNameEl.textContent = capitalize(detectedMood);
        detectedEmojiEl.textContent = moodDetails.emoji;
        clickInstruction.style.display = 'block';

        sessionStorage.setItem('detectedMoodName', detectedMood);
        sessionStorage.setItem('moodDetails', JSON.stringify(moodDetails));

        startFloatingAnimations(moodDetails.floating_emojis);

      } catch (error) {
        console.error("Error detecting mood:", error);
      }
    });

    if (moodDisplayBox) {
        moodDisplayBox.addEventListener('click', () => {
            const detectedMood = sessionStorage.getItem('detectedMoodName') || 'neutral';
            window.location.href = `/mood_details/${detectedMood}`;
        });
    }

    // REMOVED: The programmatic creation of the "Browse All Playlists" link
    // as it's now hardcoded in index.html
  }

  // --- Logic for mood_details.html (Details Page) ---
  const moodNameDetailsEl = document.getElementById("moodNameDetails");
  if (moodNameDetailsEl) {
    // Use the floatingEmojisData passed from Flask in the template
    startFloatingAnimations(window.floatingEmojisData);
  }

  // --- Logic for all_playlists.html (All Playlists Page) ---
  const allPlaylistsGrid = document.querySelector(".all-playlists-grid");
  if (allPlaylistsGrid) {
    // Use the floatingEmojisData passed from Flask in the template for all_playlists.html
    startFloatingAnimations(window.floatingEmojisData);
  }


  function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
});
