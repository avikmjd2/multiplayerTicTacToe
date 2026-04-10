const video = document.getElementById("videoFeed");
const canvas = document.getElementById('captureCanvas');
const registerBtn = document.getElementById('registerBtn');
const nameInput = document.getElementById('usernameInput');
const passwordInput = document.getElementById('passwordInput');



async function loggedIn()
{
    resp = await fetch("/auth/whoami");
    if(resp.ok) window.location.href = "/home";
}


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
            hideLoader();
            return;
        }

        updateStatus("> REGISTRATION_SUCCESS: IDENTITY_STORED");
        
        setTimeout(() => {
            window.location.href = "/login.html"; 
        }, 2000);

    } catch (err) {
        updateStatus("> ERROR: SERVER_UNREACHABLE");
        hideLoader();
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
    showLoader();
    registerUser(rawBase64, name, password);
});

 const messages = [
  "Waking up the servers...",
  "Knocking on the backend door...",
  "Summoning your data from the cloud...",
  "Polishing things up...",
  "Stretching the code a bit...",
  "Making things look awesome...",
  "Aligning pixels perfectly...",
  "Rolling for good vibes...",
  "Loading... please act impressed",
  "Almost there... we promise",
  "Just a tiny moment more..."
];

let loadingInterval = null;
function showLoader() 
{
    const overlay = document.getElementById("loading-overlay");
    const text = document.getElementById("loading-text");

    let index = 0;
    text.innerText = messages[index];

    overlay.classList.add("active");
    document.body.style.overflow = "hidden";

    loadingInterval = setInterval(() => {
      index = (index + 1) % messages.length;
      text.innerText = messages[index];
    }, 3000);
}

function hideLoader() 
{
    const overlay = document.getElementById("loading-overlay");

    overlay.classList.remove("active");
    document.body.style.overflow = "";

    if (loadingInterval) 
    {
      clearInterval(loadingInterval);
      loadingInterval = null;
    }
}
loggedIn();