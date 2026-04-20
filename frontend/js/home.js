//TODO: GOOD HOME PAGE NEEDED. COMPLETE SCRIPT.
async function fetchIdentity() {
    try {
        const res = await fetch("/auth/compdata");
        if (!res.ok) {
            window.location.href = "/login";
            return;
        }
        const data = await res.json();

        document.getElementById("greeting").textContent = `Welcome back, ${data.name}`;
        document.getElementById("subtext").textContent = `ID: ${data.uid.substring(0, 12)}...`;
        document.getElementById("elo-val").textContent = data.elo;
        document.getElementById("matches-val").textContent = data.total_played;

        // Render match history
        const logContainer = document.getElementById("match-log");
        logContainer.innerHTML = "";

        if (data.recent_matches.length === 0) {
            logContainer.innerHTML = `<div class="log-item"><span style="color: var(--text-3)">No matches played yet.</span></div>`;
            return;
        }

        // Build W/L/D summary strip
        const wins = data.recent_matches.filter(m => m.outcome === "Win").length;
        const losses = data.recent_matches.filter(m => m.outcome === "Loss").length;
        const draws = data.recent_matches.filter(m => m.outcome === "Draw").length;

        const strip = document.createElement("div");
        strip.className = "match-summary-strip";
        strip.innerHTML = `
            <span class="summary-chip s-win"><span>${wins}W</span></span>
            <span class="summary-chip s-loss"><span>${losses}L</span></span>
            <span class="summary-chip s-draw"><span>${draws}D</span></span>
        `;
        logContainer.appendChild(strip);

        data.recent_matches.forEach((match, i) => {
            const badgeClass = match.outcome === "Win" ? "badge-win"
                : match.outcome === "Loss" ? "badge-loss"
                    : "badge-draw";
            const label = match.outcome.toUpperCase();
            const time = new Date(match.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const isForfeit = match.result_type === "forfeit";

            const item = document.createElement("div");
            item.classList.add("log-item");
            item.style.animationDelay = `${i * 0.05}s`;
            item.innerHTML = `
                <div class="log-left">
                    <span class="log-time">${time}</span>
                    <span class="log-opponent">vs ${match.opponent_name}</span>
                </div>
                <div class="log-right">
                    ${isForfeit ? '<span class="log-type">FORFEIT</span>' : ''}
                    <span class="log-badge ${badgeClass}">${label}</span>
                </div>
            `;
            logContainer.appendChild(item);
        });

    } catch (err) {
        console.warn("Server unreachable.");
        document.getElementById("greeting").textContent = "Connection Lost";
    }
}

function enterLobby() {
    window.location.href = "/lobby";
}

async function logout() {
    try {
        await fetch("/auth/logout", { method: "POST" });
        window.location.href = "/login";
    } catch (e) {
        window.location.href = "/login";
    }
}

fetchIdentity();