const API_BASE_URL = "http://127.0.0.1:8000";
const accessToken = localStorage.getItem("accessToken");

document.addEventListener("DOMContentLoaded", () => {
  // Page Protection
  if (!accessToken) {
    window.location.href = "login.html";
    return;
  }
  fetchUserLibrary();
});

async function fetchUserLibrary() {
  try {
    const response = await fetch(`${API_BASE_URL}/users/me/library`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) window.location.href = "login.html";
      throw new Error("Could not fetch user library.");
    }

    const games = await response.json();
    renderLibraryGrid(games);
  } catch (error) {
    console.error(error);
  }
}

function renderLibraryGrid(games) {
  const grid = document.getElementById("library-grid");
  if (!grid) return;

  grid.innerHTML = ""; // Clear for fresh render

  // Render each game from the user's library
  games.forEach((game) => {
    const coverDiv = document.createElement("div");
    coverDiv.className = "game-cover"; // Reusing the style from onboarding

    const img = document.createElement("img");
    img.src =
      game.cover_url || "https://via.placeholder.com/264x352.png?text=No+Cover";
    img.alt = game.name;

    coverDiv.appendChild(img);
    grid.appendChild(coverDiv);
  });

  // Create and append the "Add Game" tile at the end
  const addTile = document.createElement("div");
  addTile.className = "add-game-tile";
  addTile.innerHTML = "<span>+</span>";
  // addTile.addEventListener('click', () => { /* Future logic for adding a game */ });
  grid.appendChild(addTile);
}
