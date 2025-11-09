// frontend/home.js

const API_BASE_URL = "http://127.0.0.1:8000";

document.addEventListener("DOMContentLoaded", () => {
  const accessToken = localStorage.getItem("accessToken");
  const userString = localStorage.getItem("user");

  // Page Protection
  if (!accessToken || !userString) {
    window.location.href = "login.html";
    return;
  }

  // --- Personalize Welcome Message ---
  try {
    const user = JSON.parse(userString);
    const welcomeMessage = document.getElementById("welcome-message");
    if (user && user.username) {
      const capitalizedUsername =
        user.username.charAt(0).toUpperCase() + user.username.slice(1);
      welcomeMessage.textContent = `Welcome back, ${capitalizedUsername}!`;
    }
  } catch (error) {
    console.error("Failed to parse user data from localStorage", error);
    window.location.href = "login.html";
  }

  // --- Fetch and Display Last Added Games ---
  fetchLastAddedGames(accessToken);
});

async function fetchLastAddedGames(token) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/users/me/library/last-added?limit=3`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      // If the token is invalid, redirect to login
      if (response.status === 401) {
        window.location.href = "login.html";
      }
      throw new Error("Could not fetch last added games.");
    }

    const games = await response.json();
    renderLastAddedGames(games);
  } catch (error) {
    console.error(error);
  }
}

function renderLastAddedGames(games) {
  const grid = document.getElementById("last-added-grid");
  if (!grid) return;

  grid.innerHTML = ""; // Clear any existing content

  if (games.length === 0) {
    // Optional: Display a message if the library is empty
    grid.innerHTML =
      '<p style="color: #a0a0a0;">Your library is empty. Add a game to get started!</p>';
    return;
  }

  games.forEach((game) => {
    const coverDiv = document.createElement("div");
    coverDiv.className = "game-cover-sm";

    const img = document.createElement("img");
    img.src =
      game.cover_url || "https://via.placeholder.com/264x352.png?text=No+Cover";
    img.alt = game.name;

    coverDiv.appendChild(img);
    grid.appendChild(coverDiv);
  });
}
