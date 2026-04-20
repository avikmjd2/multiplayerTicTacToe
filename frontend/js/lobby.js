
const playerContainer = document.getElementById("player-container");
const occupancyText = document.getElementById("occupancy-text");
const systemMsg = document.getElementById("lobby-msg");
const readyBtn = document.getElementById("ready-toggle");


let myUid = null;

systemMsg.innerText = "System: Establishing secure uplink...";
let socket = null;
let reconnectTimeout = null;
let reconnectAttempts =0;
const MAX_RECONNECT_DELAY = 5000;
const challengePrompt = document.getElementById('challenge-prompt');
const acceptBtn = document.querySelector('.accept-btn');
const declineBtn = document.querySelector('.decline-btn');


function connectToLobby(){
    socket = new WebSocket(`ws://${window.location.host}/ws/lobby`)   
    
    socket.onopen = () => 
    {
        systemMsg.innerText = "System: Connected to Lobby. Challenge Other Users Now!";
        reconnectAttempts = 0;
    };
    
    
    socket.onclose = (event) =>{
        console.log(event)
        // if(event.code===1008 || event.code===1006)
        if(event.code===1008)
        {
            window.location.href = "/";
        }
        else 
        {
            console.log("Disconnected from the Arena.");
            triggerReconnect();
        }
    }

    
    socket.onmessage = (event) =>{
        const data = JSON.parse(event.data)
        // console.log(data)
    
        if (data.type === "identity") 
        {
            myUid = data.my_uid;
        }
        if (data.type === "presence") 
        {
            updateLobbyUI(data);
        }
        if(data.type==="ask")
        {
            ask(data);
        }
        if(data.type==="challenge")
        {
            const room = data.room_id;
            if(room ==="error")
            {
                challengePrompt.style.display = 'none';
                systemMsg.innerText = "Some error occured. Please try again after sometime.";
                
            }
            else if(room==="decline" )
            {
                challengePrompt.style.display = 'none';
                systemMsg.innerText = "Challenge Declined By The Recipient";
                
            }
            else if(room === "timeout") 
            {
                challengePrompt.style.display = 'none';
                systemMsg.innerText = "Challenge Timed Out. No response received.";
            }
            else
            {
                console.log(room);
                window.location.href = `/game/${room}`;
    
            }
        }
    
    }

    
}



function ask(data)
{   
    if(data.opp_uid==="0000" && data.opp_name==="Currently_Busy")
    {
        systemMsg.innerText = "Player Currently Engaged in a Challenge. Please Try Again Later."
        return;
    }
    challengePrompt.style.display = 'flex';
    challengePrompt.querySelector('.player-name').textContent = data.opp_name;
    challengePrompt.querySelector('.challenger-avatar').textContent = data.opp_name.substr(0,1);
    challengePrompt.querySelector(".player-id").textContent = data.elo_rating
    challengePrompt.dataset.uid = data.opp_uid;
}

acceptBtn.addEventListener('click', function(e) 
{
    e.preventDefault();
    console.log("Challenge Accepted! Sending response to server...");
    const payload = {
        "action": "accept_challenge",
        "opp_uid": challengePrompt.dataset.uid,
        "accepted": "accepted"
    }
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(payload));
        // systemMsg.innerText = "System: Readiness signal transmitted...";
        systemMsg.innerText = "Status: Match accepted. Preparing board...";
    } 
    else 
    {
        systemMsg.innerText = "System: Cannot send, uplink offline.";
    }
    challengePrompt.style.display = 'none';
    
});

declineBtn.addEventListener('click', function(e) 
{
    e.preventDefault()
    console.log("Challenge Accepted! Sending response to server...");
    const payload = {
        "action": "accept_challenge",
        "opp_uid": challengePrompt.dataset.uid,
        "accepted": "declined"
    }
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(payload));
        // systemMsg.innerText = "System: Readiness signal transmitted...";
        systemMsg.innerText = "Status: Challenge declined.";
    } 
    else 
    {
        systemMsg.innerText = "System: Cannot send, uplink offline.";
    }
    challengePrompt.style.display = 'none';
});




function updateLobbyUI(data)
{
    occupancyText.innerText = `${data.count} Players Online Now`;
    // playerContainer.innerHTML = "";
    const incomingUids = data.users.map(u => u.uid);
    Array.from(playerContainer.children).forEach(card=>{
        if (!incomingUids.includes(card.dataset.uid) && !card.classList.contains("is-deleting")) {
            card.classList.add("is-deleting"); 
            card.style.opacity = "0";
            card.style.transform = "scale(0.9)";
            setTimeout(() => {
                if(card.parentNode && card.classList.contains("is-deleting")) 
                {
                    card.remove();
                }
            }, 200);
        }
    })


    // console.log(data);
    data.users.forEach((user,index) => {
        const initial = user.name.charAt(0).toUpperCase();
        let readyClass = user.is_ready ? "is-ready" : "";
        let readyText = user.is_ready ? "READY" : "STANDBY";

        const isHost = (myUid === user.uid);
        let hostControls = "";
        let disableTag="";

        if (isHost) 
        {
            if (user.is_ready) 
            {
                readyBtn.classList.add("nowready");
                readyBtn.innerText = "Cancel Ready";
            }
            else 
            {
                readyBtn.classList.remove("nowready");
                readyBtn.innerText = "Initialize Ready";
            }
        }

        if (user.room_id) 
        {
            readyText = "BUSY";
            readyClass = "is-busy"; 
            disableTag = "disabled";
        }
        else if (isHost || !user.is_ready) 
        {
            // const disableTag = allReady ? "" : "disabled";
                disableTag= "disabled";
            
        }
        let existingCard = document.querySelector(`.player-card[data-uid="${user.uid}"]`);
        if (existingCard) 
        {
            if (existingCard.classList.contains("is-deleting")) 
            { 
                existingCard.classList.remove("is-deleting");
                existingCard.style.opacity = "1";
                existingCard.style.transform = "scale(1)";
            }

            const statusDiv = existingCard.querySelector('.ready-status');
            statusDiv.className = `ready-status ${readyClass}`;
            statusDiv.innerText = readyText;

            const btn = existingCard.querySelector('.play-btn-mini');
            if (btn) 
            {
                if (disableTag) btn.setAttribute('disabled', 'true');
                else btn.removeAttribute('disabled');
            }
        }

        else
        {
            hostControls = `
                <button class="play-btn-mini" ${disableTag} data-uid="${user.uid}">
                    Engage Match
                </button>
            `;
            
            // <span class="player-id">ID: ${user.uid.substring(0, 8)}...</span>

            const cardHTML = `
                <div class="player-card ${isHost ? 'host-card' : ''}" data-uid="${user.uid}">
                    <div class="avatar">${initial}</div>
                    <span class="player-name">${isHost ? 'Me: ' : ''} ${user.name} </span>
                    <div class="ready-status ${readyClass}">${readyText}</div>
                    ${hostControls}
                </div>
            `;
            playerContainer.insertAdjacentHTML('beforeend', cardHTML);

        }
    });

    // systemMsg.innerText = "Ready."; //MAYBE TODO:ii

}








readyBtn.addEventListener('click',()=>{
    if(!socket || socket.readyState !== WebSocket.OPEN)
    {
        systemMsg.innerText = "System: Cannot send, uplink offline.";
        return;
    }
    //nowready means the player is ready, clicking makes it non ready
    
    let  payload = { action: "toggle_ready" };
    if(readyBtn.classList.contains("nowready"))
    {
        // console.log("here1")
        payload = {action: "non_ready"};
        readyBtn.classList.toggle("nowready");
        readyBtn.innerText = "initialize Ready"
        systemMsg.innerText = "Status: You are currently on standby.";
        
    }
    else
    {
        // console.log("here2")
        payload = {action: "toggle_ready"};
        readyBtn.classList.toggle("nowready");
        readyBtn.innerText = "Non_Ready";
        systemMsg.innerText = "Status: You are queued and ready to play.";
    }


    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(payload));
        // systemMsg.innerText = "System: Readiness signal transmitted...";
    } 
    else 
    {
        systemMsg.innerText = "System: Cannot send, uplink offline.";
    }
})



playerContainer.addEventListener("click",(e)=>{
    const btn = e.target.closest(".play-btn-mini");
    if(!btn) return;
    const player_uid = btn.dataset.uid;
    // console.log(player_uid);

    const payload = {
        "action": "challenge_player",
        "opp_uid": player_uid
    }
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(payload));
        // systemMsg.innerText = "System: Readiness signal transmitted...";
        systemMsg.innerText = "Status: Challenge sent. Waiting for response...";
    } 
    else 
    {
        systemMsg.innerText = "System: Cannot send, uplink offline.";
    }
})

function triggerReconnect() 
{
    clearTimeout(reconnectTimeout);

    let delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY);
    reconnectAttempts++;

    console.log(`Reconnecting in ${delay / 1000} seconds...`);
    systemMsg.innerText = "Connection Lost: Reconnecting ..... (PS: Check Internet Connection)";

    reconnectTimeout = setTimeout(() => {
        connectToLobby();
    }, delay);

}


connectToLobby();