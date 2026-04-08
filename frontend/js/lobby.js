

const playerContainer = document.getElementById("player-container");
const occupancyText = document.getElementById("occupancy-text");
const systemMsg = document.getElementById("lobby-msg");
const readyBtn = document.getElementById("ready-toggle");


let myUid = null;

systemMsg.innerText = "System: Establishing secure uplink...";
const socket = new WebSocket(`ws://${window.location.host}/ws/lobby`)


socket.onopen = () => 
{
    systemMsg.innerText = "System: Connected to Global Lobby 01.";
};


socket.onclose = (event) =>{
    console.log(event)
    if(event.code===1008 || event.code===1006)
    {
        window.location.href = "/";
    }
    else 
    {
        console.log("Disconnected from the Arena.");
    }
}

const challengePrompt = document.getElementById('challenge-prompt');
const acceptBtn = document.querySelector('.accept-btn');
const declineBtn = document.querySelector('.decline-btn');

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
            systemMsg.innerText = "CHALLENGE DECLINED";
            
        }
        else
        {
            console.log(room);
            //traverse to room network;
        }
    }

}


function ask(data)
{    
    challengePrompt.style.display = 'flex';
    challengePrompt.querySelector('.player-name').textContent = data.opp_name;
    challengePrompt.querySelector('.challenger-avatar').textContent = data.opp_name.substr(0,1);
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
        systemMsg.innerText = "System: Readiness signal transmitted...";
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
        systemMsg.innerText = "System: Readiness signal transmitted...";
    } 
    else 
    {
        systemMsg.innerText = "System: Cannot send, uplink offline.";
    }
    challengePrompt.style.display = 'none';
});




function updateLobbyUI(data)
{
    occupancyText.innerText = `${data.count}/10 Combatants`;
    playerContainer.innerHTML = "";
    // console.log(data);
    data.users.forEach((user,index) => {
        const initial = user.name.charAt(0).toUpperCase();
        let readyClass = user.is_ready ? "is-ready" : "";
        let readyText = user.is_ready ? "READY" : "STANDBY";

        const isHost = (myUid === user.uid);
        let hostControls = "";
        let disableTag="";


        if (user.room_id !== null) 
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
        hostControls = `
            <button class="play-btn-mini" ${disableTag} data-uid="${user.uid}">
                Engage Match
            </button>
        `;

        const cardHTML = `
            <div class="player-card ${isHost ? 'host-card' : ''}">
                <div class="avatar">${initial}</div>
                <span class="player-name">${user.name} ${isHost ? '👑' : ''}</span>
                <span class="player-id">ID: ${user.uid.substring(0, 8)}...</span>
                <div class="ready-status ${readyClass}">${readyText}</div>
                ${hostControls}
            </div>
        `;
        playerContainer.insertAdjacentHTML('beforeend', cardHTML);
    });

    // systemMsg.innerText = "Ready."; //MAYBE TODO:ii

}


readyBtn.addEventListener('click',()=>{
    if(socket.readyState !== WebSocket.OPEN)
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
        
    }
    else
    {
        // console.log("here2")
        payload = {action: "toggle_ready"};
        readyBtn.classList.toggle("nowready");
        readyBtn.innerText = "Non_Ready"
    }


    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(payload));
        systemMsg.innerText = "System: Readiness signal transmitted...";
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
        systemMsg.innerText = "System: Readiness signal transmitted...";
    } 
    else 
    {
        systemMsg.innerText = "System: Cannot send, uplink offline.";
    }
})