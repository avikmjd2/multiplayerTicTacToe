const INTERVAL = 30;
let secondsLeft = INTERVAL;
let countdownTimer = null;

async function loadLeaderboard() {
  try {
    const res = await fetch("/api/leaderboard");
    if (!res.ok) throw new Error("Failed to fetch");
    const players = await res.json();

    allPlayers = players;         // hand data to the search layer
    renderFiltered(currentQuery); // re-render respecting any active query

    // Update podium
    if (players.length >= 1) {
      document.getElementById("pod-1-name").textContent = players[0].name;
      document.getElementById("pod-1-elo").textContent  = players[0].elo_rating.toLocaleString();
    }
    if (players.length >= 2) {
      document.getElementById("pod-2-name").textContent = players[1].name;
      document.getElementById("pod-2-elo").textContent  = players[1].elo_rating.toLocaleString();
    }
    if (players.length >= 3) {
      document.getElementById("pod-3-name").textContent = players[2].name;
      document.getElementById("pod-3-elo").textContent  = players[2].elo_rating.toLocaleString();
    }
    if (players.length >= 3) {
      document.getElementById("podium").style.display = "grid";
    }

    document.querySelector(".live-badge").classList.remove("error");
  } catch (err) {
    const tbody = document.getElementById("leaderboard-body");
    tbody.innerHTML = `<tr><td colspan="3" class="state err">Failed to load leaderboard.</td></tr>`;
    document.querySelector(".live-badge").classList.add("error");
  }
}

function startCountdown() {
  clearInterval(countdownTimer);
  secondsLeft = INTERVAL;
  const el = document.getElementById("countdown");
  countdownTimer = setInterval(() => {
    secondsLeft--;
    el.textContent = `Refreshes in ${secondsLeft}s`;
    if (secondsLeft <= 0) {
      secondsLeft = INTERVAL;
      loadLeaderboard();
    }
  }, 1000);
}

function manualRefresh() {
  const btn = document.getElementById("refresh-btn");
  btn.classList.add("spinning");
  setTimeout(() => btn.classList.remove("spinning"), 450);
  loadLeaderboard();
  startCountdown();
}

loadLeaderboard();
startCountdown();