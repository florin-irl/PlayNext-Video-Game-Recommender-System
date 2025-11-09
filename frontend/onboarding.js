const API_BASE_URL = "http://127.0.0.1:8000";
const accessToken = localStorage.getItem("accessToken");
const selectedGameIds = new Set();

const doneBtn = document.getElementById("done-btn");
const gamesGrid = document.getElementById("games-grid");

document.addEventListener("DOMContentLoaded", () => {
  // Protect the page: if not logged in, redirect to login
  if (!accessToken) {
    window.location.href = "login.html";
    return;
  }
  fetchOnboardingGames();

  doneBtn.addEventListener("click", submitSelection);
});

async function fetchOnboardingGames() {
  try {
    const response = await fetch(`${API_BASE_URL}/games/onboarding`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error("Could not fetch games.");
    }

    const games = await response.json();
    renderGamesGrid(games);
  } catch (error) {
    alert(`Error: ${error.message}`);
    // If token is invalid, redirect to login
    if (error.message.includes("401")) {
      window.location.href = "login.html";
    }
  }
}

function renderGamesGrid(games) {
  gamesGrid.innerHTML = ""; // Clear existing grid
  games.forEach((game) => {
    const coverDiv = document.createElement("div");
    coverDiv.className = "game-cover";
    coverDiv.dataset.gameId = game.id; // Store game ID on the element

    const img = document.createElement("img");
    img.src =
      game.cover_url || "https://via.placeholder.com/264x352.png?text=No+Cover";
    img.alt = game.name;

    coverDiv.appendChild(img);
    coverDiv.addEventListener("click", () => toggleSelection(coverDiv));
    gamesGrid.appendChild(coverDiv);
  });
}

function toggleSelection(coverDiv) {
  const gameId = parseInt(coverDiv.dataset.gameId, 10);

  if (selectedGameIds.has(gameId)) {
    selectedGameIds.delete(gameId);
    coverDiv.classList.remove("selected");
  } else {
    if (selectedGameIds.size < 5) {
      selectedGameIds.add(gameId);
      coverDiv.classList.add("selected");
    } else {
      alert("You can only select up to 5 games.");
    }
  }
  updateDoneButtonState();
}

function updateDoneButtonState() {
  const count = selectedGameIds.size;
  doneBtn.textContent = `Done (${count}/5)`;

  if (count === 5) {
    doneBtn.disabled = false;
  } else {
    doneBtn.disabled = true;
  }
}

async function submitSelection() {
  try {
    const response = await fetch(
      `${API_BASE_URL}/users/me/library/initialize`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ game_ids: Array.from(selectedGameIds) }),
      }
    );

    if (!response.ok) {
      throw new Error("Failed to submit selection.");
    }

    // Update user's status in localStorage to avoid showing this page again
    const user = JSON.parse(localStorage.getItem("user"));
    user.is_initialized = true;
    localStorage.setItem("user", JSON.stringify(user));

    alert("Library created successfully!");
    window.location.href = "home.html"; // Redirect to the main app
  } catch (error) {
    alert(`Error: ${error.message}`);
  }
}
