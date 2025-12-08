const API_BASE_URL = "http://127.0.0.1:8000";
const accessToken = localStorage.getItem("accessToken");

// --- MODIFICATION: Declare variables that will hold the modal elements ---
let detailsModal;
let detailsModalContent;
let detailsModalCloseBtn;

// --- Main execution ---
document.addEventListener("DOMContentLoaded", () => {
  if (!accessToken) {
    window.location.href = "login.html";
    return;
  }

  // --- MODIFICATION: Find the modal elements *after* the DOM is loaded ---
  detailsModal = document.getElementById("game-details-modal");
  detailsModalContent = document.getElementById("game-details-content");
  detailsModalCloseBtn = document.getElementById("details-modal-close-btn");

  // Now that we're sure the elements exist, we can set them up
  fetchAndRenderRecommendations();
  setupDetailsModal();
});

// --- API Calls ---
async function fetchAndRenderRecommendations() {
  const container = document.getElementById("recommendations-container");
  container.innerHTML =
    '<p style="color: #a0a0a0;">Generating your recommendations...</p>';
  try {
    const seedGamesResponse = await fetch(
      `${API_BASE_URL}/users/me/library/last-added?limit=3`,
      {
        headers: { Authorization: `Bearer ${accessToken}` },
      }
    );
    if (!seedGamesResponse.ok)
      throw new Error("Could not fetch your recent games.");
    const seedGames = await seedGamesResponse.json();

    if (seedGames.length === 0) {
      container.innerHTML =
        '<p style="color: #a0a0a0;">Your library is empty. Add games to get recommendations!</p>';
      return;
    }

    const recommendationPromises = seedGames.map((game) =>
      fetch(`${API_BASE_URL}/recommendations/${game.id}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      }).then((res) => {
        if (!res.ok) return [];
        return res.json();
      })
    );
    const recommendationsByGame = await Promise.all(recommendationPromises);
    renderAllRows(seedGames, recommendationsByGame);
  } catch (error) {
    console.error(error);
    container.innerHTML =
      '<p style="color: #ff6b6b;">Failed to load recommendations.</p>';
  }
}

// --- DOM Rendering ---
function renderAllRows(seedGames, recommendationsByGame) {
  const container = document.getElementById("recommendations-container");
  container.innerHTML = "";

  seedGames.forEach((seedGame, index) => {
    const recommendations = recommendationsByGame[index];
    if (!recommendations || recommendations.length === 0) return;

    const rowDiv = document.createElement("div");
    rowDiv.className = "recommendation-row";
    rowDiv.innerHTML = `<h2 class="recommendation-title">Because you played <span class="rec-seed-game">${seedGame.name}</span></h2>`;
    const carouselDiv = document.createElement("div");
    carouselDiv.className = "games-carousel";

    recommendations.forEach((recGame) => {
      const coverDiv = document.createElement("div");
      coverDiv.className = "game-cover";
      coverDiv.dataset.gameId = recGame.id;
      coverDiv.innerHTML = `<img src="${
        recGame.cover_url ||
        "https://via.placeholder.com/264x352.png?text=No+Cover"
      }" alt="${recGame.name}">`;
      coverDiv.addEventListener("click", () =>
        openGameDetailsModal(recGame.id)
      );
      carouselDiv.appendChild(coverDiv);
    });

    rowDiv.appendChild(carouselDiv);
    container.appendChild(rowDiv);
  });
}

// --- Details Modal Logic ---
function setupDetailsModal() {
  // Check if the modal was actually found before adding listeners
  if (detailsModalCloseBtn) {
    detailsModalCloseBtn.addEventListener("click", closeGameDetailsModal);
  }
  if (detailsModal) {
    detailsModal.addEventListener("click", (e) => {
      if (e.target === detailsModal) closeGameDetailsModal();
    });
  }
}

async function openGameDetailsModal(gameId) {
  // Defensive check
  if (!detailsModal || !detailsModalContent) return;

  detailsModal.classList.add("visible");
  detailsModalContent.innerHTML =
    '<p style="color: #a0a0a0; text-align: center;">Loading details...</p>';

  try {
    const response = await fetch(`${API_BASE_URL}/games/${gameId}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (!response.ok) throw new Error("Could not fetch game details.");

    const game = await response.json();
    renderGameDetails(game);
  } catch (error) {
    console.error(error);
    detailsModalContent.innerHTML =
      '<p style="color: #ff6b6b; text-align: center;">Failed to load details.</p>';
  }
}

function renderGameDetails(game) {
  if (!detailsModalContent) return;
  detailsModalContent.innerHTML = `
        <div class="details-cover">
            <img src="${
              game.cover_url ||
              "https://via.placeholder.com/264x352.png?text=No+Cover"
            }" alt="${game.name}">
        </div>
        <div class="details-info">
            <h2>${game.name}</h2>
            <p>${game.summary || "No summary available."}</p>
            <button class="add-to-library-btn" data-game-id="${
              game.id
            }">Add to Library</button>
        </div>
    `;
  detailsModalContent
    .querySelector(".add-to-library-btn")
    .addEventListener("click", handleAddToLibrary);
}

function closeGameDetailsModal() {
  if (!detailsModal) return;
  detailsModal.classList.remove("visible");
  detailsModalContent.innerHTML = "";
}

async function handleAddToLibrary(event) {
  const button = event.target;
  const gameId = parseInt(button.dataset.gameId, 10);
  button.disabled = true;
  button.textContent = "Adding...";

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
      closeGameDetailsModal();
      return;
    }
    if (!response.ok) throw new Error("Failed to add game.");

    closeGameDetailsModal();

    const coverToRemove = document.querySelector(
      `.game-cover[data-game-id='${gameId}']`
    );
    if (coverToRemove) {
      coverToRemove.style.transition = "opacity 0.3s ease";
      coverToRemove.style.opacity = "0";
      setTimeout(() => coverToRemove.remove(), 300);
    }
  } catch (error) {
    alert(error.message);
    button.disabled = false;
    button.textContent = "Add to Library";
  }
}
