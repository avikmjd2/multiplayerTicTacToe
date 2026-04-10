const video = document.getElementById("videoFeed")

async function loggedIn()
{
    resp = await fetch("/auth/whoami");
    if(resp.ok) window.location.href = "/home";
}

async function startCam() 
{
    try{
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 640, height: 480 }, 
            audio: false 
        });
        video.srcObject = stream;
        updateStatus("> CAMERA_CONNECTED: LIVE_FEED_ACTIVE");
    }catch (err) 
    {
        console.error("Error accessing camera:", err);
        updateStatus("> ERROR: CAMERA_ACCESS_DENIED");
    }
}

async function loginAtpt(img) 
{
    body = {image:img}
    const resp = await fetch("/auth/login",{
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    })

    if(!resp.ok)
    {
        updateStatus("> Unverified User Spotted...");
        hideLoader();
        return;
    }

    // const data = await resp.json();
    window.location.href = "/home";
}


function updateStatus(msg) 
{
    document.getElementById('statusMessage').innerText = msg;
}


startCam();

const canvas = document.getElementById('captureCanvas');
const captureBtn = document.getElementById('captureBtn');

captureBtn.addEventListener('click',()=>{
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const base64Image = canvas.toDataURL('image/jpeg');
    // console.log("Captured Image String:", base64Image);
    const rawBase64 = base64Image.split(",")[1];
    updateStatus("> FRAME_CAPTURED: ANALYZING...");
    showLoader();
    loginAtpt(rawBase64);
})


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