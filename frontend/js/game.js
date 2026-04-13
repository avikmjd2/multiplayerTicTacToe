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
        updateBoard(data.board, data.win_line);
        updateStatus(data.turn, data.status);
    }
};

// Render the 3x3 board
function updateBoard(boardGrid, winLine) {
    // Remove any existing win line overlay
    const existingLine = document.querySelector('.win-line-overlay');
    if (existingLine) existingLine.remove();

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

    // Highlight winning cells + draw line
    if (winLine && winLine.length === 3) {
        // Add win-cell class to winning cells
        winLine.forEach(([r, c]) => {
            const winCell = document.querySelector(`.cell[data-row="${r}"][data-col="${c}"]`);
            if (winCell) winCell.classList.add("win-cell");
        });

        // Draw SVG line through winning cells after a brief delay for animation
        setTimeout(() => drawWinLine(winLine), 200);
    }
}

// Draw an SVG line overlay through the center of the winning cells
function drawWinLine(winLine) {
    const board = document.getElementById("board");
    const boardRect = board.getBoundingClientRect();

    const firstCell = document.querySelector(`.cell[data-row="${winLine[0][0]}"][data-col="${winLine[0][1]}"]`);
    const lastCell = document.querySelector(`.cell[data-row="${winLine[2][0]}"][data-col="${winLine[2][1]}"]`);

    if (!firstCell || !lastCell) return;

    const firstRect = firstCell.getBoundingClientRect();
    const lastRect = lastCell.getBoundingClientRect();

    // Calculate start and end points relative to the board
    const x1 = (firstRect.left + firstRect.width / 2) - boardRect.left;
    const y1 = (firstRect.top + firstRect.height / 2) - boardRect.top;
    const x2 = (lastRect.left + lastRect.width / 2) - boardRect.left;
    const y2 = (lastRect.top + lastRect.height / 2) - boardRect.top;

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("win-line-overlay");
    svg.setAttribute("width", boardRect.width);
    svg.setAttribute("height", boardRect.height);
    svg.style.position = "absolute";
    svg.style.top = "0";
    svg.style.left = "0";
    svg.style.pointerEvents = "none";
    svg.style.zIndex = "100";

    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", x1);
    line.setAttribute("y1", y1);
    line.setAttribute("x2", x2);
    line.setAttribute("y2", y2);

    // Use CSS style properties (not SVG attributes) so CSS transition works
    line.style.stroke = "#4a443f";
    line.style.strokeWidth = "8";
    line.style.filter = "drop-shadow(0px 1px 2px rgba(0,0,0,0.2))";

    // Set up dash animation via CSS style properties
    const length = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
    line.style.strokeDasharray = length;
    line.style.strokeDashoffset = length;
    line.style.transition = "stroke-dashoffset 0.5s ease-out";

    svg.appendChild(line);
    board.appendChild(svg);

    // Trigger the draw animation on next frame
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            line.style.strokeDashoffset = "0";
        });
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