const API_BASE_URL = "http://127.0.0.1:8000";
const accessToken = localStorage.getItem("accessToken");

document.addEventListener("DOMContentLoaded", () => {
  // Page Protection
  if (!accessToken) {
    window.location.href = "login.html";
    return;
  }
  fetchAndRenderRecommendations();
});

async function fetchAndRenderRecommendations() {
  const container = document.getElementById("recommendations-container");
  container.innerHTML =
    '<p style="color: #a0a0a0;">Generating your recommendations...</p>';

  try {
    // Step 1: Get the user's last 3 added games (our "seed" games)
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

    // Step 2: For each seed game, fetch its 10 recommendations.
    // We use Promise.all to run these requests in parallel for speed.
    const recommendationPromises = seedGames.map((game) =>
      fetch(`${API_BASE_URL}/recommendations/${game.id}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      }).then((res) => res.json())
    );

    const recommendationsByGame = await Promise.all(recommendationPromises);

    // Step 3: Render the results
    renderAllRows(seedGames, recommendationsByGame);
  } catch (error) {
    console.error(error);
    container.innerHTML =
      '<p style="color: #ff6b6b;">Failed to load recommendations.</p>';
  }
}

function renderAllRows(seedGames, recommendationsByGame) {
  const container = document.getElementById("recommendations-container");
  container.innerHTML = ""; // Clear the loading message

  seedGames.forEach((seedGame, index) => {
    const recommendations = recommendationsByGame[index];
    if (!recommendations || recommendations.length === 0) return;

    // Create the container for the entire row
    const rowDiv = document.createElement("div");
    rowDiv.className = "recommendation-row";

    // Create the title (e.g., "Because you played Minecraft")
    const title = document.createElement("h2");
    title.className = "recommendation-title";
    title.innerHTML = `Because you played <span class="rec-seed-game">${seedGame.name}</span>`;

    // Create the horizontally-scrolling carousel
    const carouselDiv = document.createElement("div");
    carouselDiv.className = "games-carousel";

    // Populate the carousel with game covers
    recommendations.forEach((recGame) => {
      const coverDiv = document.createElement("div");
      coverDiv.className = "game-cover";

      const img = document.createElement("img");
      img.src =
        recGame.cover_url ||
        "https://via.placeholder.com/264x352.png?text=No+Cover";
      img.alt = recGame.name;

      coverDiv.appendChild(img);
      carouselDiv.appendChild(coverDiv);
    });

    rowDiv.appendChild(title);
    rowDiv.appendChild(carouselDiv);
    container.appendChild(rowDiv);
  });
}
