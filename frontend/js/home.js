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

        data.recent_matches.forEach(match => {
            const color = match.outcome === "Win" ? "var(--success)"
                : match.outcome === "Loss" ? "var(--danger)"
                    : "var(--accent)";
            const label = match.outcome.toUpperCase();
            const time = new Date(match.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            const item = document.createElement("div");
            item.classList.add("log-item");
            item.innerHTML = `
                <span style="color: var(--text-3)">[${time}]</span>
                <span>vs ${match.opponent_name}</span>
                <span style="color: ${color}">${label}</span>
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