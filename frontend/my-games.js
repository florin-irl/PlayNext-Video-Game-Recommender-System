// frontend/my-games.js

const API_BASE_URL = "http://127.0.0.1:8000";
const accessToken = localStorage.getItem("accessToken");

// --- Main execution on page load ---
document.addEventListener("DOMContentLoaded", () => {
  if (!accessToken) {
    window.location.href = "login.html";
    return;
  }
  fetchUserLibrary();
  setupModal();
});

// --- Library Rendering ---
async function fetchUserLibrary() {
  try {
    const response = await fetch(`${API_BASE_URL}/users/me/library`, {
      headers: { Authorization: `Bearer ${accessToken}` },
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
  grid.innerHTML = "";

  games.forEach((game) => {
    const coverDiv = document.createElement("div");
    coverDiv.className = "game-cover";
    const img = document.createElement("img");
    img.src =
      game.cover_url || "https://via.placeholder.com/264x352.png?text=No+Cover";
    img.alt = game.name;
    coverDiv.appendChild(img);
    grid.appendChild(coverDiv);
  });

  const addTile = document.createElement("div");
  addTile.className = "add-game-tile";
  addTile.innerHTML = "<span>+</span>";
  addTile.addEventListener("click", openModal); // Event listener to open modal
  grid.appendChild(addTile);
}

// --- Modal Logic ---
const modalOverlay = document.getElementById("add-game-modal");
const closeBtn = document.getElementById("modal-close-btn");
const searchInput = document.getElementById("game-search-input");
const searchResultsContainer = document.getElementById("search-results");
let debounceTimer;

function setupModal() {
  closeBtn.addEventListener("click", closeModal);
  modalOverlay.addEventListener("click", (event) => {
    if (event.target === modalOverlay) closeModal(); // Close if clicking outside the content
  });
  searchInput.addEventListener("input", (event) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      handleSearch(event.target.value);
    }, 300); // 300ms debounce
  });
}

function openModal() {
  modalOverlay.classList.add("visible");
}

function closeModal() {
  modalOverlay.classList.remove("visible");
  searchInput.value = ""; // Clear search input on close
  searchResultsContainer.innerHTML = ""; // Clear results on close
}

// --- Search and Add Logic ---
async function handleSearch(query) {
  if (query.length < 3) {
    searchResultsContainer.innerHTML = "";
    return;
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/games/search?q=${encodeURIComponent(query)}`,
      {
        headers: { Authorization: `Bearer ${accessToken}` },
      }
    );
    if (!response.ok) throw new Error("Search failed.");
    const games = await response.json();
    renderSearchResults(games);
  } catch (error) {
    console.error(error);
    searchResultsContainer.innerHTML =
      '<p style="color: #a0a0a0;">Error searching for games.</p>';
  }
}

function renderSearchResults(games) {
  searchResultsContainer.innerHTML = "";
  if (games.length === 0) {
    searchResultsContainer.innerHTML =
      '<p style="color: #a0a0a0;">No games found.</p>';
    return;
  }

  games.forEach((game) => {
    const item = document.createElement("div");
    item.className = "search-result-item";
    item.innerHTML = `
            <img src="${
              game.cover_url ||
              "https://via.placeholder.com/264x352.png?text=N/A"
            }" alt="${game.name}">
            <p>${game.name}</p>
        `;
    item.addEventListener("click", () => addGameToLibrary(game.id));
    searchResultsContainer.appendChild(item);
  });
}

async function addGameToLibrary(gameId) {
  try {
    const response = await fetch(`${API_BASE_URL}/users/me/library`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ game_id: gameId }),
    });

    if (response.status === 409) {
      alert("This game is already in your library.");
      return;
    }
    if (!response.ok) {
      throw new Error("Failed to add game.");
    }

    // Success!
    closeModal();
    fetchUserLibrary(); // Refresh the grid to show the new game
  } catch (error) {
    console.error(error);
    alert(error.message);
  }
}
