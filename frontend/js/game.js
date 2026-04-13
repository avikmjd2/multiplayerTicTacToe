// Extract room_id from the URL path, e.g. /game/room_123 -> room_123
const pathParts = window.location.pathname.split("/");
const roomId = pathParts[pathParts.length - 1];

// WebSocket connection (opening persistent connection)
const socket = new WebSocket(`ws://${window.location.host}/ws/game/${roomId}`);

// UI Elements
const statusEl = document.getElementById("game-status");
const symbolEl = document.getElementById("player-symbol");
const cells = document.querySelectorAll(".cell");
const actionsPanel = document.getElementById("actions-panel");

let mySymbol = null; // X or O or SPECTATOR
let currentGameState = "waiting";

// Handle Socket Open
socket.onopen = () => {
    statusEl.innerText = "Waiting for opponent...";
    statusEl.className = "game-status status-waiting";
};

// Handle Socket Close/Disconnect
socket.onclose = () => {
    if (!currentGameState.startsWith("win_") && !currentGameState.startsWith("forfeit_") && currentGameState !== "draw") {
        setStatus("Connection Lost", "status-lose");
        showReturnButton();
    }
};

// Handle Incoming Server Messages
socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "init") {
        mySymbol = data.symbol;
        symbolEl.innerText = `Playing as ${mySymbol}`;
        symbolEl.style.opacity = "1";
    }
    else if (data.type === "update") {
        updateBoard(data.board);
        updateStatus(data.turn, data.status);
    }
};

// Render the 3x3 board
function updateBoard(boardGrid) {
    cells.forEach(cell => {
        const r = parseInt(cell.getAttribute("data-row"));
        const c = parseInt(cell.getAttribute("data-col"));

        const cellValue = boardGrid[r][c];
        cell.innerText = cellValue;

        // Reset classes
        cell.className = "cell";

        if (cellValue !== "") {
            cell.classList.add("occupied");
            if (cellValue === "X") cell.classList.add("x-mark");
            if (cellValue === "O") cell.classList.add("o-mark");
        }
    });
}

// Smooth status text updater with fade transition
function setStatus(text, className) {
    statusEl.style.opacity = "0";
    setTimeout(() => {
        statusEl.innerText = text;
        statusEl.className = `game-status ${className}`;
        statusEl.style.opacity = "1";
    }, 150);
}

// Update the status text based on whose turn / game state
function updateStatus(turn, status) {
    currentGameState = status;

    if (status === "waiting") {
        setStatus("Waiting for opponent...", "status-waiting");
    }
    else if (status === "playing") {
        if (turn === mySymbol) {
            setStatus(`Your Turn (${mySymbol})`, "status-my-turn");
        } else {
            setStatus(`Player ${turn}'s Turn`, "status-opponent-turn");
        }
    }
    else if (status.startsWith("win_")) {
        const winnerSymbol = status.split("_")[1];
        if (winnerSymbol === mySymbol) {
            setStatus("You Win!", "status-win");
        } else {
            setStatus("You Lose", "status-lose");
        }
        showReturnButton();
    }
    else if (status === "draw") {
        setStatus("It's a Draw", "status-draw");
        showReturnButton();
    }
    else if (status.startsWith("forfeit_")) {
        const quitter = status.split("_")[1];
        if (quitter === mySymbol) {
            setStatus("You Disconnected", "status-lose");
        } else {
            setStatus("Opponent Left — You Win!", "status-win");
        }
        showReturnButton();
    }
}

// Click Listeners for sending moves
cells.forEach(cell => {
    cell.addEventListener("click", () => {
        // Validation before bothering the Server
        if (!mySymbol) return;
        if (currentGameState !== "playing") return;
        if (cell.classList.contains("occupied")) return;

        const r = parseInt(cell.getAttribute("data-row"));
        const c = parseInt(cell.getAttribute("data-col"));

        // Emit payload to server
        socket.send(JSON.stringify({
            action: "move",
            row: r,
            col: c
        }));
    });
});

// Show return button with smooth entrance
function showReturnButton() {
    actionsPanel.style.display = "block";
    // Disable further cell clicks visually
    cells.forEach(cell => {
        if (!cell.classList.contains("occupied")) {
            cell.style.cursor = "default";
            cell.style.opacity = "0.7";
        }
    });
}