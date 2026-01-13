const API_BASE_URL = "http://127.0.0.1:8000";
const accessToken = localStorage.getItem("accessToken");

document.addEventListener("DOMContentLoaded", () => {
  // Page Protection
  if (!accessToken) {
    window.location.href = "login.html";
    return;
  }
  fetchPopularGames();
});

async function fetchPopularGames() {
  const grid = document.getElementById("popular-grid");
  if (!grid) return;
  grid.innerHTML = '<p style="color: #a0a0a0;">Loading popular games...</p>';

  try {
    const response = await fetch(`${API_BASE_URL}/games/popular`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });

    if (!response.ok) {
      if (response.status === 401) window.location.href = "login.html";
      throw new Error("Could not fetch popular games.");
    }

    const games = await response.json();
    renderPopularGrid(games);
  } catch (error) {
    console.error(error);
    grid.innerHTML =
      '<p style="color: #ff6b6b;">Failed to load popular games.</p>';
  }
}

function renderPopularGrid(games) {
  const grid = document.getElementById("popular-grid");
  grid.innerHTML = ""; // Clear loading message

  games.forEach((game) => {
    // Main container for the card (cover + info)
    const card = document.createElement("div");
    card.className = "popular-game-card";

    // Re-use the .game-cover style for the image part
    const coverDiv = document.createElement("div");
    coverDiv.className = "game-cover";
    const img = document.createElement("img");
    img.src =
      game.cover_url || "https://via.placeholder.com/285x380.png?text=No+Cover";
    img.alt = game.name;
    coverDiv.appendChild(img);

    // Container for the info below the cover
    const infoDiv = document.createElement("div");
    infoDiv.className = "game-info";

    card.appendChild(coverDiv);
    card.appendChild(infoDiv);

    grid.appendChild(card);
  });
}
