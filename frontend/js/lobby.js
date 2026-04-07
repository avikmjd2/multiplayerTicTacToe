

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


socket.onmessage = (event) =>{
    const data = JSON.parse(event.data)

    if (data.type === "identity") 
    {
        myUid = data.my_uid;
    }
    if (data.type === "presence") 
    {
        updateLobbyUI(data);
    }
}


function updateLobbyUI(data)
{
    occupancyText.innerText = `${data.count}/10 Combatants`;
    playerContainer.innerHTML = "";
    data.users.forEach((user,index) => {
        const initial = user.name.charAt(0).toUpperCase();
        const readyClass = user.is_ready ? "is-ready" : "";
        const readyText = user.is_ready ? "READY" : "STANDBY";

        const isHost = (myUid === user.uid);
        let hostControls = "";
        let disableTag="";
        if (isHost) 
        {
            // const disableTag = allReady ? "" : "disabled";
             disableTag= "disabled";
            
        }
        hostControls = `
            <button class="play-btn-mini" ${disableTag} id = "play-btn" data-uid="('${user.uid}')">
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

    systemMsg.innerText = "Ready.";

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
    console.log(player_uid);
})