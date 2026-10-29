// =============================================================================
// 1. Seitenparameter und Elemente
// =============================================================================

const parameters = new URLSearchParams(window.location.search);

const gameId = parameters
    .get("game_id")
    ?.toUpperCase() ?? null;

const playerIndexParameter = parameters.get("player_index");

const playerIndex = playerIndexParameter === null ? Number.NaN : Number(playerIndexParameter);


// Allgemeine Anzeigeelemente.
const gameIdElement = document.getElementById("game-id");

const connectionStatus = document.getElementById("connection-status");

const turnStatus = document.getElementById("turn-status");

const errorMessage = document.getElementById("error-message");

const gameNotificationElement = document.getElementById("game-notification");

// Spielfeld und Spielerinformationen.
const boardElement = document.getElementById("board");

const spareTileElement = document.getElementById("spare-tile");

const playerListElement = document.getElementById("player-list");

const currentTargetElement = document.getElementById("current-target");


// Charakter und Charakterfähigkeit.
const characterNameElement = document.getElementById("character-name");

const abilityStatusElement = document.getElementById("ability-status");

const magicianAbilityControls = document.getElementById("magician-ability-controls");

const magicianRotateLeftButton = document.getElementById("magician-rotate-left-button");

const magicianRotateRightButton = document.getElementById("magician-rotate-right-button");


// Zugstatus und Bedienelemente.
const turnStepShift = document.getElementById("turn-step-shift");

const turnStepMove = document.getElementById("turn-step-move");

const turnStepEnd = document.getElementById("turn-step-end");

const turnStepShiftText = document.getElementById("turn-step-shift-text");

const turnStepMoveText = document.getElementById("turn-step-move-text");

const turnStepEndText = document.getElementById("turn-step-end-text");

const shiftControlsElement = document.getElementById("shift-controls");

const rotateSpareButton = document.getElementById("rotate-spare-button");

const endTurnButton = document.getElementById("end-turn-button");

const gameOverOverlay = document.getElementById("game-over-overlay");

const gameOverTitle = document.getElementById("game-over-title");

const gameOverText = document.getElementById("game-over-text");

// GUI-Elemente
const TILE_IMAGES = {
    straight: "/static/assets/tiles/straight.png",
    corner: "/static/assets/tiles/corner.png",
    t_junction: "/static/assets/tiles/t_junction.png",
    cross: "/static/assets/tiles/cross.png"
};

const SPECIAL_IMAGES = {
    portal: "/static/assets/special/portal.png"
};

const GATE_IMAGES = {
    leaf_closed: "/static/assets/gates/leaf_closed.png",
    leaf_open: "/static/assets/gates/leaf_open.png",
    moon_closed: "/static/assets/gates/moon_closed.png",
    moon_open: "/static/assets/gates/moon_open.png"
};

const TARGET_IMAGES = {
    "Eule": "/static/assets/targets/eule.png",
    "Blattschlüssel": "/static/assets/targets/blattschluessel.png",
    "Drache": "/static/assets/targets/drache.png",
    "Eidechse": "/static/assets/targets/eidechse.png",
    "Fledermaus": "/static/assets/targets/fledermaus.png",
    "Geldbeutel": "/static/assets/targets/geldbeutel.png",
    "Hirschschädel": "/static/assets/targets/hirschschaedel.png",
    "Irrlicht": "/static/assets/targets/irrlicht.png",
    "Karte": "/static/assets/targets/karte.png",
    "Krone": "/static/assets/targets/krone.png",
    "Laterne": "/static/assets/targets/laterne.png",
    "Leuchtkäfer": "/static/assets/targets/leuchtkaefer.png",
    "Maus": "/static/assets/targets/maus.png",
    "Mondschlüssel": "/static/assets/targets/mondschluessel.png",
    "Motte": "/static/assets/targets/motte.png",
    "Ring": "/static/assets/targets/ring.png",
    "Schwert": "/static/assets/targets/schwert.png",
    "Smaragd": "/static/assets/targets/smaragd.png",
    "Spinne": "/static/assets/targets/spinne.png",
    "Truhe": "/static/assets/targets/truhe.png",
    "Waldgeist": "/static/assets/targets/waldgeist.png",
    "Waldhüter": "/static/assets/targets/waldhueter.png",
    "Wicht": "/static/assets/targets/wicht.png",
    "Zauberin": "/static/assets/targets/zauberin.png"
};


// Aktive WebSocket-Verbindung.
let websocket = null;


// Zuletzt empfangene Zustände.
let latestGameState = null;
let latestPlayerState = null;


// Magier-Zustand.
let magicianSelectionMode = false;
let magicianRotationDirection = null;


// Ungültige oder unvollständige URLs führen
// zurück zur Startseite.
if (!gameId || !Number.isInteger(playerIndex) || playerIndex < 0) {
    window.location.href = "/";
}


// =============================================================================
// 2. Allgemeine Hilfsfunktionen
// =============================================================================

async function requestJson(url, options = {}) {
    const response = await fetch(url, options);

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail ?? "Unbekannter Fehler.");
    }

    return data;
}


function sendAction(message) {
    errorMessage.textContent = "";

    if (websocket === null || websocket.readyState !== WebSocket.OPEN) {
        errorMessage.textContent = "Keine Verbindung zum Server.";

        return;
    }

    websocket.send(JSON.stringify(message));
}


function getTileSymbol(tileType) {
    switch (tileType) {
        case "straight":
            return "┃";

        case "corner":
            return "┗";

        case "t_junction":
            return "┻";

        case "cross":
            return "╋";

        default:
            return "?";
    }
}


function cancelMagicianSelection() {
    magicianSelectionMode = false;
    magicianRotationDirection = null;

    if (latestGameState !== null) {
        renderBoard(latestGameState);
    }
}


function startMagicianSelection(direction) {
    if (latestPlayerState === null || !latestPlayerState.ability_available) {
        return;
    }

    magicianSelectionMode = true;

    magicianRotationDirection = direction;

    if (latestGameState !== null) {
        renderBoard(latestGameState);
    }
}

let gameNotificationTimeout = null;


function showGameNotification(message, type = "default") {
    if (gameNotificationTimeout !== null) {
        clearTimeout(gameNotificationTimeout);
    }

    gameNotificationElement.textContent = message;

    gameNotificationElement.className = "game-notification";

    gameNotificationElement.classList.add(`game-notification-${type}`);

    gameNotificationElement.hidden = false;


    gameNotificationTimeout = setTimeout(() => {
        gameNotificationElement.hidden = true;

        gameNotificationTimeout = null;
    }, 2200);
}

function handleGameEvent(event) {
    switch (event.event) {

        case "target_completed":
            showGameNotification(`Ziel gefunden: ${event.target}`, "success");
            break;


        case "key_activated": {
            const gateName = event.key === "Blattschlüssel" ? "Blatttor" : "Mondtor";

            showGameNotification(`${event.key} gefunden – ${gateName} geöffnet!`, "success");

            break;
        }


        case "portal_used":
            showGameNotification("Portal benutzt", "portal");
            break;
    }
}

// =============================================================================
// 3. Rendering des Spielzustands
// =============================================================================

function createTileElement(tile, row = null, column = null, reachablePositions = [], allowMovement
= false, allowMagicianAbility = false) {
    const element = document.createElement("div");

    element.classList.add("tile", `tile-${tile.tile_type}`);


    if (tile.fixed) {
        element.classList.add("tile-fixed");
    }

    if (tile.portal) {
        element.classList.add("tile-portal");
    }

    if (tile.gate !== null) {
        element.classList.add("tile-gate");

        element.classList.add(tile.gate_open ? "gate-open" : "gate-closed");
    }


    // Pfad
    const pathElement = document.createElement("div");

    pathElement.classList.add("tile-path");

    appendImageWithFallback(pathElement, TILE_IMAGES[tile.tile_type] ?? null, "tile-path-image",
        "", getTileSymbol(tile.tile_type));

    pathElement.style.transform = `rotate(${tile.rotation * 90}deg)`;

    element.appendChild(pathElement);


    // Target / Portal / Tor
    const overlay = document.createElement("div");

    overlay.classList.add("tile-overlay");


    if (tile.portal) {
        appendImageWithFallback(overlay, SPECIAL_IMAGES.portal, "tile-portal-image", "Portal",
            "🌀");

    } else if (tile.gate !== null) {
        const gateState = tile.gate_open ? "open" : "closed";

        const gateKey = `${tile.gate}_${gateState}`;

        appendImageWithFallback(overlay, GATE_IMAGES[gateKey] ?? null, "tile-gate-image",
            `${tile.gate} gate`, tile.gate === "leaf" ? "🌿" : "🌙");

    } else if (tile.target !== null) {
        appendImageWithFallback(overlay, TARGET_IMAGES[tile.target] ?? null, "tile-target-image",
            tile.target, tile.target);
    }

    element.appendChild(overlay);


    // Board-Kachel
    if (row !== null && column !== null) {
        element.dataset.row = row;
        element.dataset.column = column;


        // Magier-Auswahl
        if (allowMagicianAbility) {
            element.classList.add("tile-magician-selectable");

            element.title = magicianRotationDirection === "left" ? "Diese Kachel nach links drehen"
                : "Diese Kachel nach rechts drehen";

            element.addEventListener("click", () => {
                const direction = magicianRotationDirection;

                if (direction === null) {
                    return;
                }

                magicianSelectionMode = false;

                magicianRotationDirection = null;

                sendAction({
                    type: "use_magician_ability", row: row, column: column, direction: direction
                });
            });

            return element;
        }


        const reachable = reachablePositions.some(position => position.row === row
            && position.column === column);

        if (reachable && allowMovement) {
            element.classList.add("tile-reachable");
            element.title = "Figur hierhin bewegen";

            element.addEventListener("click", () => {
                sendAction({
                    type: "move", row: row, column: column
                });
            });
        }
    }

    return element;
}

function renderBoard(state) {
    boardElement.innerHTML = "";

    const isMyTurn = state.current_player_index === playerIndex;


    const allowMagicianAbility = magicianSelectionMode && latestPlayerState !== null &&
        latestPlayerState.ability_available && isMyTurn && !state.finished;


    const allowMovement = isMyTurn && state.has_shifted && !state.has_moved && !state.finished && !allowMagicianAbility;


    for (let row = 0; row < state.board.tiles.length; row++) {
        for (let column = 0; column < state.board.tiles[row].length; column++) {
            const tile = state.board.tiles[row][column];

            const tileElement = createTileElement(tile, row, column, state.reachable_positions,
                allowMovement, allowMagicianAbility && !tile.fixed);


            const playersHere = state.players.filter(player => player.row === row && player.column === column);

            if (playersHere.length > 0) {
                const playerContainer = document.createElement("div");

                playerContainer.classList.add("players-on-tile");

                for (const player of playersHere) {
                    const marker = document.createElement("span");

                    marker.classList.add("player-marker", `player-marker-${player.player_index + 1}`);

                    if (player.player_index === state.current_player_index) {
                        marker.classList.add("player-marker-active");
                    }

                    marker.textContent = player.player_index + 1;

                    marker.title = player.character !== null ? `${player.name} – ${player.character}` : player.name;

                    playerContainer.appendChild(marker);
                }

                tileElement.appendChild(playerContainer);
            }

            boardElement.appendChild(tileElement);
        }
    }
}


function renderSpareTile(state) {
    spareTileElement.innerHTML = "";

    const tileElement = createTileElement(state.board.spare_tile);

    tileElement.classList.add("spare-tile");

    spareTileElement.appendChild(tileElement);
}


function renderPlayers(state) {
    playerListElement.innerHTML = "";

    for (const player of state.players) {
        const listItem = document.createElement("li");

        listItem.classList.add("player-list-entry");


        // Spielstein
        const marker = document.createElement("span");

        marker.classList.add("player-marker", `player-marker-${player.player_index + 1}`);

        if (player.player_index === state.current_player_index) {
            marker.classList.add("player-marker-active");
        }

        marker.textContent = player.player_index + 1;


        // Textbereich
        const information = document.createElement("div");

        information.classList.add("player-list-info");


        // Spielername + DU
        const nameRow = document.createElement("div");

        nameRow.classList.add("player-list-name-row");


        const name = document.createElement("strong");

        name.textContent = player.name;

        nameRow.appendChild(name);


        if (player.player_index === playerIndex) {
            const selfBadge = document.createElement("span");

            selfBadge.classList.add("player-self-badge");

            selfBadge.textContent = "DU";

            nameRow.appendChild(selfBadge);
        }


        // Charakter
        const character = document.createElement("span");

        character.textContent = player.character ?? "Kein Charakter";


        // Gefundene Ziele
        const targets = document.createElement("span");

        const completedTargets = player.completed_targets?.length ?? 0;

        targets.textContent = completedTargets === 1 ? "1 Ziel gefunden" : `${completedTargets} Ziele gefunden`;


        information.append(nameRow, character, targets);

        listItem.append(marker, information);

        playerListElement.appendChild(listItem);
    }
}


function renderTurnState(state) {

    // Spiel beendet
    if (state.finished) {
        const winnerNumber = state.winner_index !== null ? state.winner_index + 1 : "?";

        turnStatus.textContent = `Spiel beendet – Spieler ${winnerNumber} hat gewonnen.`;

        setTurnStepState(turnStepShift, "completed");

        setTurnStepState(turnStepMove, "completed");

        setTurnStepState(turnStepEnd, "completed");

        turnStepShiftText.textContent = "Abgeschlossen";

        turnStepMoveText.textContent = "Abgeschlossen";

        turnStepEndText.textContent = "Spiel beendet";

        return;
    }


    const isMyTurn = state.current_player_index === playerIndex;


    if (!isMyTurn) {
        const currentPlayer = state.players.find(player => player.player_index === state.current_player_index);

        turnStatus.textContent = `${currentPlayer?.name ?? "Ein anderer Spieler"} ` + "ist am Zug.";

        setTurnStepState(turnStepShift, "pending");

        setTurnStepState(turnStepMove, "pending");

        setTurnStepState(turnStepEnd, "pending");

        turnStepShiftText.textContent = "Warten";

        turnStepMoveText.textContent = "Warten";

        turnStepEndText.textContent = "Warten";

        return;
    }


    turnStatus.textContent = "Du bist am Zug.";


    // Schritt 1
    if (!state.has_shifted) {
        setTurnStepState(turnStepShift, "active");

        setTurnStepState(turnStepMove, "pending");

        setTurnStepState(turnStepEnd, "pending");

        turnStepShiftText.textContent = "Jetzt ausführen";

        turnStepMoveText.textContent = "Nach dem Verschieben";

        turnStepEndText.textContent = "Noch nicht verfügbar";

        return;
    }


    setTurnStepState(turnStepShift, "completed");

    turnStepShiftText.textContent = "Abgeschlossen";


    // Schritt 2
    if (!state.has_moved) {
        setTurnStepState(turnStepMove, "active");

        setTurnStepState(turnStepEnd, "available");

        turnStepMoveText.textContent = "Optional";

        turnStepEndText.textContent = "Bereits möglich";

        return;
    }


    setTurnStepState(turnStepMove, "completed");

    setTurnStepState(turnStepEnd, "active");

    turnStepMoveText.textContent = "Abgeschlossen";

    turnStepEndText.textContent = "Jetzt möglich";
}


function setTurnStepState(element, state) {
    element.classList.remove("turn-step-pending", "turn-step-active", "turn-step-available",
        "turn-step-completed");

    element.classList.add(`turn-step-${state}`);
}


function renderPlayerState(state) {
    latestPlayerState = state;


    // Persönliches Ziel
    currentTargetElement.innerHTML = "";

    if (state.current_target === null) {
        currentTargetElement.textContent = "Alle Ziele abgeschlossen – zurück zum Startfeld!";

    } else {
        appendImageWithFallback(currentTargetElement, TARGET_IMAGES[state.current_target] ?? null,
            "current-target-image", state.current_target, state.current_target);

        currentTargetElement.title = state.current_target;
    }


    // Charakter
    characterNameElement.textContent = state.character ?? "Kein Charakter";


    // Magier
    if (state.character === "Magier") {
        magicianAbilityControls.hidden = false;

        magicianRotateLeftButton.disabled = !state.ability_available;

        magicianRotateRightButton.disabled = !state.ability_available;


        if (state.ability_used_for_current_target) {
            abilityStatusElement.textContent = "Fähigkeit für dieses Ziel bereits verwendet.";

        } else if (state.ability_available) {
            abilityStatusElement.textContent = "Aktive Fähigkeit: Eine bewegliche Board-Kachel "
                + "kann einmal nach links oder rechts gedreht werden.";

        } else {
            abilityStatusElement.textContent = "Fähigkeit aktuell nicht einsetzbar.";
        }


        if (!state.ability_available) {
            magicianSelectionMode = false;

            magicianRotationDirection = null;
        }

        // Wächter
    } else if (state.character === "Wächter") {
        magicianAbilityControls.hidden = true;

        magicianRotateLeftButton.disabled = true;

        magicianRotateRightButton.disabled = true;

        magicianSelectionMode = false;

        magicianRotationDirection = null;

        abilityStatusElement.textContent = "Passive Fähigkeit: Geschlossene Tore "
            + "können ohne Schlüssel passiert werden.";

    } else {
        magicianAbilityControls.hidden = true;

        magicianRotateLeftButton.disabled = true;

        magicianRotateRightButton.disabled = true;

        magicianSelectionMode = false;

        magicianRotationDirection = null;

        abilityStatusElement.textContent = "";
    }


    if (latestGameState !== null) {
        renderBoard(latestGameState);
    }
}

function renderShiftControls(state) {
    shiftControlsElement.innerHTML = "";

    const isMyTurn = state.current_player_index === playerIndex;

    if (!isMyTurn || state.finished) {
        return;
    }


    for (const shift of state.board.allowed_shifts) {
        const button = document.createElement("button");

        button.type = "button";

        button.classList.add("shift-button", `shift-${shift.direction}`);

        button.dataset.index = shift.index;


        switch (shift.direction) {
            case "east":
                button.textContent = "→";

                button.title = `Reihe ${shift.index} von links einschieben`;

                break;

            case "west":
                button.textContent = "←";

                button.title = `Reihe ${shift.index} von rechts einschieben`;

                break;

            case "south":
                button.textContent = "↓";

                button.title = `Spalte ${shift.index} von oben einschieben`;

                break;

            case "north":
                button.textContent = "↑";

                button.title = `Spalte ${shift.index} von unten einschieben`;

                break;
        }


        button.addEventListener("click", () => {
            cancelMagicianSelection();

            sendAction({
                type: "shift", index: shift.index, direction: shift.direction
            });
        });

        shiftControlsElement.appendChild(button);
    }
}


function renderControls(state) {
    const isMyTurn = state.current_player_index === playerIndex;


    rotateSpareButton.disabled = !isMyTurn || state.has_shifted || state.finished;


    endTurnButton.disabled = !isMyTurn || !state.has_shifted || state.finished;


    renderShiftControls(state);
}

function renderGameOverOverlay(state) {
    if (!state.finished) {
        gameOverOverlay.hidden = true;

        return;
    }


    const winner = state.players.find(player => player.player_index === state.winner_index);


    const winnerName = winner?.name ?? `Spieler ${state.winner_index + 1}`;


    if (state.winner_index === playerIndex) {
        gameOverTitle.textContent = "Du hast gewonnen!";

        gameOverText.textContent = "Du hast alle Ziele gefunden " + "und dein Startfeld wieder erreicht.";

    } else {
        gameOverTitle.textContent = `${winnerName} gewinnt!`;

        gameOverText.textContent = `${winnerName} hat alle Ziele gefunden ` + "und das Startfeld wieder erreicht.";
    }


    gameOverOverlay.hidden = false;
}

function renderGameState(state) {
    const previousState = latestGameState;

    latestGameState = state;

    if (previousState !== null && !state.finished && previousState.current_player_index !== state.current_player_index) {
        const currentPlayer = state.players.find(player => player.player_index === state.current_player_index);

        if (state.current_player_index === playerIndex) {
            showGameNotification("Du bist am Zug", "turn");

        } else {
            showGameNotification(`${currentPlayer?.name ?? "Ein anderer Spieler"} ist am Zug`, "turn");
        }
    }

    if (state.finished || state.current_player_index !== playerIndex) {
        magicianSelectionMode = false;

        magicianRotationDirection = null;
    }


    renderBoard(state);

    renderSpareTile(state);

    renderPlayers(state);

    renderTurnState(state);

    renderControls(state);

    renderGameOverOverlay(state);
}


function appendImageWithFallback(container, source, className, altText, fallbackText) {
    if (!source) {
        container.textContent = fallbackText;

        container.classList.add("asset-fallback");

        return;
    }


    const image = document.createElement("img");

    image.src = source;

    image.alt = altText;

    image.draggable = false;

    image.classList.add("tile-asset-image", className);

    image.addEventListener("error", () => {
        image.remove();

        container.textContent = fallbackText;

        container.classList.add("asset-fallback");
    }, {
        once: true
    });

    container.appendChild(image);
}


// =============================================================================
// 4. REST- und WebSocket-Kommunikation
// =============================================================================

async function loadInitialGameState() {
    try {
        const state = await requestJson(`/games/${gameId}`);

        renderGameState(state);

    } catch (error) {
        errorMessage.textContent = error.message;
    }
}


function handleWebSocketMessage(message) {
    if (message.type === "game_state") {
        renderGameState(message.data);

    } else if (message.type === "player_state") {
        renderPlayerState(message.data);

    } else if (message.type === "error") {
        cancelMagicianSelection();

        errorMessage.textContent = message.message;

    } else if (message.type === "action_success") {
        if (message.action === "use_magician_ability") {
            cancelMagicianSelection();

            showGameNotification("Magierfähigkeit eingesetzt", "magic");
        }


        if (Array.isArray(message.events)) {
            for (const gameEvent of message.events) {
                handleGameEvent(gameEvent);
            }
        }


        console.log("Aktion erfolgreich:", message.action);
    }
}


function connectWebSocket() {
    const websocketProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";

    const websocketUrl = `${websocketProtocol}//` + `${window.location.host}` + `/ws/games/${gameId}`
        + `/players/${playerIndex}`;

    websocket = new WebSocket(websocketUrl);


    websocket.addEventListener("open", () => {
        connectionStatus.textContent = "verbunden";
    });


    websocket.addEventListener("close", event => {
        connectionStatus.textContent = "getrennt";

        cancelMagicianSelection();

        console.error("WebSocket geschlossen:", event.code, event.reason);
    });


    websocket.addEventListener("error", event => {
        connectionStatus.textContent = "Fehler";

        console.error("WebSocket-Fehler:", event);
    });


    websocket.addEventListener("message", event => {
        try {
            const message = JSON.parse(event.data);

            handleWebSocketMessage(message);

        } catch (error) {
            console.error("Ungültige WebSocket-Nachricht:", error);
        }
    });
}

// =============================================================================
// 5. Benutzeraktionen und Initialisierung
// =============================================================================

function registerEventListeners() {
    rotateSpareButton.addEventListener("click", () => {
        cancelMagicianSelection();

        sendAction({
            type: "rotate_spare_tile"
        });
    });


    endTurnButton.addEventListener("click", () => {
        cancelMagicianSelection();

        sendAction({
            type: "end_turn"
        });
    });


    magicianRotateLeftButton.addEventListener("click", () => {
        startMagicianSelection("left");
    });


    magicianRotateRightButton.addEventListener("click", () => {
        startMagicianSelection("right");
    });
}


function initializeGamePage() {
    gameIdElement.textContent = gameId;


    /*
     * Bis der erste private Player-State
     * empfangen wurde, werden die
     * Magier-Bedienelemente ausgeblendet.
     */
    magicianAbilityControls.hidden = true;

    magicianRotateLeftButton.disabled = true;

    magicianRotateRightButton.disabled = true;


    characterNameElement.textContent = "Wird geladen...";

    abilityStatusElement.textContent = "Wird geladen...";


    registerEventListeners();

    connectWebSocket();

    loadInitialGameState();
}


initializeGamePage();