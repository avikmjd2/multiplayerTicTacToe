// Extract room_id from the URL path, e.g. /game/room_123 -> room_123
const pathParts = window.location.pathname.split("/");
const roomId = pathParts[pathParts.length - 1];

// WebSocket connection (opening persistent connection)
const socket = new WebSocket(`ws://${window.location.host}/ws/game/${roomId}`);

// UI Elements (fetching all at once)
const statusEl = document.getElementById("game-status");
const symbolEl = document.getElementById("player-symbol");
const cells = document.querySelectorAll(".cell");
const actionsPanel = document.getElementById("actions-panel");

let mySymbol = null; // X or O or SPECTATOR
let currentGameState = "waiting";

// Handle Socket Open (runs when connection established)
socket.onopen = () => {
    statusEl.innerText = "WAITING FOR COMBATANT...";
    statusEl.className = "game-status status-waiting";
};

// Handle Socket Close/Disconnect (runs when disconnect, shows error only when game not ended cause on end, disconnect expected)
socket.onclose = () => {
    if (currentGameState !== "win" && currentGameState !== "lose" && currentGameState !== "draw") {
        statusEl.innerText = "SERVER CONNECTION LOST";
        statusEl.className = "game-status status-lose";
        showReturnButton();
    }
};

// Handle Incoming Server Messages
socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "init") {
        mySymbol = data.symbol;
        symbolEl.innerText = `YOU ARE [ ${mySymbol} ]`;
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

// Update the Top Text based on whose turn it is
function updateStatus(turn, status) {
    currentGameState = status;

    if (status === "waiting") {
        statusEl.innerText = "WAITING FOR OPPONENT...";
        statusEl.className = "game-status status-waiting";
    }
    else if (status === "playing") {
        if (turn === mySymbol) {
            statusEl.innerText = "> YOUR TURN <";
            statusEl.className = "game-status status-my-turn";
        } else {
            statusEl.innerText = "OPPONENT COMPUTING...";
            statusEl.className = "game-status status-opponent-turn";
        }
    }
    else if (status.startsWith("win_")) {
        // e.g. "win_X"
        const winnerSymbol = status.split("_")[1];
        if (winnerSymbol === mySymbol) {
            statusEl.innerText = "VICTORY ACHIEVED";
            statusEl.className = "game-status status-win";
        } else {
            statusEl.innerText = "MATCH FAILED";
            statusEl.className = "game-status status-lose";
        }
        showReturnButton();
    }
    else if (status === "draw") {
        statusEl.innerText = "STALEMATE RESOLVED";
        statusEl.className = "game-status status-draw";
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

function showReturnButton() {
    actionsPanel.style.display = "block";
}
