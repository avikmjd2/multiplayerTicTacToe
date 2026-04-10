const INTERVAL = 30;
let secondsLeft = INTERVAL;
let countdownTimer = null;

async function loadLeaderboard() {
  const tbody = document.getElementById("leaderboard-body");
  try {
    const res = await fetch("/api/leaderboard");
    if (!res.ok) throw new Error("Failed to fetch");
    const players = await res.json();
    if (players.length === 0) {
      tbody.innerHTML = `<tr><td colspan="3" class="loading">No players yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = players.map((p, i) => {
      const rank = i + 1;
      const medal = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : rank;
      const rowClass = rank <= 3 ? `top-${rank}` : "";
      return `<tr class="${rowClass}">
        <td class="rank">${medal}</td>
        <td class="name">${p.name}</td>
        <td class="elo">${p.elo_rating.toLocaleString()}</td>
      </tr>`;
    }).join("");
    document.querySelector(".live-badge").classList.remove("error");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="3" class="error">Failed to load leaderboard.</td></tr>`;
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

loadLeaderboard();
startCountdown();