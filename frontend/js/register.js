const video = document.getElementById("videoFeed");
const canvas = document.getElementById('captureCanvas');
const registerBtn = document.getElementById('registerBtn');
const nameInput = document.getElementById('usernameInput');
const passwordInput = document.getElementById('passwordInput');

async function startCam() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 640, height: 480 }, 
            audio: false 
        });
        video.srcObject = stream;
        updateStatus("> CAMERA_CONNECTED: AWAITING_INPUT");
    } catch (err) {
        updateStatus("> ERROR: CAMERA_ACCESS_DENIED");
    }
}

async function registerUser(img, username, password) {
    const body = { name: username, password: password, image: img };
    
    try {
        const resp = await fetch("/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        if (!resp.ok) {
            const errorData = await resp.json();
            updateStatus(`> ERROR: ${errorData.detail || "REGISTRATION_FAILED"}`);
            return;
        }

        updateStatus("> REGISTRATION_SUCCESS: IDENTITY_STORED");
        
        setTimeout(() => {
            window.location.href = "/login.html"; 
        }, 2000);

    } catch (err) {
        updateStatus("> ERROR: SERVER_UNREACHABLE");
    }
}

function updateStatus(msg) {
    document.getElementById('statusMessage').innerText = msg;
}

startCam();

registerBtn.addEventListener('click', () => {
    const name = nameInput.value.trim();
    const password = passwordInput.value.trim();

    if (!name || !password) {
        updateStatus("> ERROR: MISSING_CREDENTIALS");
        return;
    }

    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const base64Image = canvas.toDataURL('image/jpeg');
    const rawBase64 = base64Image.split(",")[1];
    
    updateStatus("> FRAME_CAPTURED: TRANSMITTING_DATA...");
    registerUser(rawBase64, name, password);
});