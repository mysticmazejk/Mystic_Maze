// =============================================================================
// 1. Seitenparameter und DOM-Elemente
// =============================================================================

const parameters = new URLSearchParams(
    window.location.search
);

const gameId = parameters
    .get("game_id")
    ?.toUpperCase() ?? null;

const playerIndexParameter = parameters.get(
    "player_index"
);

const playerIndex =
    playerIndexParameter === null
        ? Number.NaN
        : Number(playerIndexParameter);


// Allgemeine Lobbyinformationen.
const gameIdElement = document.getElementById(
    "game-id"
);

const copyGameIdButton =
    document.getElementById(
        "copy-game-id-button"
    );

const copyGameIdStatus =
    document.getElementById(
        "copy-game-id-status"
    );

const playerIndexElement = document.getElementById(
    "player-index"
);

const connectionStatus = document.getElementById(
    "connection-status"
);

const errorMessage = document.getElementById(
    "error-message"
);


// Spieler- und Spielstatus.
const playerList = document.getElementById(
    "player-list"
);

const gameStatus = document.getElementById(
    "game-status"
);

// Charakterauswahl.
const characterSelect = document.getElementById(
    "character-select"
);

const selectCharacterButton = document.getElementById(
    "select-character-button"
);

const characterDescription = document.getElementById(
    "character-description"
);


// Elemente zum Starten des Spiels.
const startSection = document.getElementById(
    "start-section"
);

const startGameForm = document.getElementById(
    "start-game-form"
);

const targetsPerPlayerInput = document.getElementById(
    "targets-per-player"
);

const startGameButton = document.getElementById(
    "start-game-button"
);


// Aktive WebSocket-Verbindung.
// Sie wird erst bei der Initialisierung aufgebaut.
let websocket = null;


// Ungültige oder unvollständige URLs führen
// zurück zur Startseite.
if (
    !gameId
    || !Number.isInteger(playerIndex)
    || playerIndex < 0
) {
    window.location.href = "/";
}


// =============================================================================
// 2. Allgemeine Hilfsfunktionen
// =============================================================================

/**
 * Führt einen HTTP-Request aus und gibt die geparste JSON-Antwort zurück.
 *
 * Bei einer fehlerhaften HTTP-Antwort wird die vom Backend
 * übermittelte Fehlermeldung als Exception weitergegeben.
 *
 * @param {string} url - Ziel-URL des Requests.
 * @param {RequestInit} [options={}] - Optionen für fetch(),
 *                                     z. B. Methode oder Body.
 * @returns {Promise<Object>} Geparste JSON-Antwort des Servers.
 * @throws {Error} Wenn der Server einen HTTP-Fehler zurückgibt.
 */
async function requestJson(
    url,
    options = {}
) {
    const response = await fetch(
        url,
        options
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.detail ?? "Unbekannter Fehler."
        );
    }

    return data;
}


/**
 * Zeigt eine Fehlermeldung in der Lobby an.
 *
 * @param {string} message - Anzuzeigende Fehlermeldung.
 */
function showError(message) {
    errorMessage.textContent = message;
}


/**
 * Entfernt eine zuvor angezeigte Fehlermeldung.
 */
function clearError() {
    errorMessage.textContent = "";
}


/**
 * Öffnet die eigentliche Spielansicht.
 *
 * Spiel-ID und Spielerindex werden als URL-Parameter weitergegeben,
 * damit game.js die richtige Partie und den richtigen Spieler kennt.
 */
function openGame() {
    const url = new URL(
        "/static/game.html",
        window.location.origin
    );

    url.searchParams.set(
        "game_id",
        gameId
    );

    url.searchParams.set(
        "player_index",
        playerIndex
    );

    window.location.href =
        url.toString();
}


// =============================================================================
// 3. Rendering der Lobby
// =============================================================================

/**
 * Rendert die Spielerliste der Lobby.
 *
 * Neben dem Namen wird auch der aktuell gewählte Charakter angezeigt.
 *
 * @param {Array<Object>} players - Öffentlich sichtbare Spielerzustände.
 */
function renderPlayers(players) {
    playerList.innerHTML = "";

    for (const player of players) {
        const item = document.createElement(
            "li"
        );

        const character =
            player.character
            ?? "noch kein Charakter";

        let text =
            `${player.name} `
            + `(Spieler ${player.player_index})`
            + ` – ${character}`;

        if (
            player.player_index
            === playerIndex
        ) {
            text += " – Du";
        }

        item.textContent = text;

        playerList.appendChild(
            item
        );
    }
}


/**
 * Zeigt die Beschreibung des momentan
 * im Auswahlfeld gewählten Charakters an.
 */
function renderCharacterDescription() {
    switch (characterSelect.value) {
        case "Magier":
            characterDescription.textContent =
                "Kann einmal pro gesuchtem Ziel "
                + "eine Kachel auf dem Spielfeld drehen.";
            break;

        case "Wächter":
            characterDescription.textContent =
                "Kann geschlossene Tore auch ohne "
                + "den passenden Schlüssel passieren.";
            break;

        default:
            characterDescription.textContent =
                "Bitte wähle einen Charakter.";
    }
}


/**
 * Aktualisiert die Charakterauswahl anhand
 * des öffentlichen Spielzustands.
 *
 * Charaktere, die bereits von einem anderen Spieler gewählt
 * wurden, werden im Auswahlfeld deaktiviert.
 *
 * Der eigene bereits gewählte Charakter bleibt weiterhin
 * auswählbar, damit seine aktuelle Auswahl sichtbar bleibt.
 *
 * @param {Object} state - Öffentlicher Spielzustand.
 */
function renderCharacterSelection(state) {
    const currentPlayer = state.players.find(
        player =>
            player.player_index === playerIndex
    );

    if (!currentPlayer) {
        return;
    }


    for (
        const option
        of characterSelect.options
    ) {
        // Der leere Platzhalter ist kein echter Charakter.
        if (!option.value) {
            continue;
        }

        const selectedByOtherPlayer =
            state.players.some(
                player =>
                    player.player_index !== playerIndex
                    && player.character === option.value
            );

        option.disabled =
            selectedByOtherPlayer;
    }


    // Die serverseitig gespeicherte Auswahl
    // auch im Select-Feld anzeigen.
    characterSelect.value =
        currentPlayer.character ?? "";


    // Nach dem Spielstart darf die Charakterauswahl
    // nicht mehr verändert werden.
    characterSelect.disabled =
        state.started;

    selectCharacterButton.disabled =
        state.started;


    renderCharacterDescription();
}


/**
 * Aktualisiert die Startmöglichkeit des Hosts.
 *
 * Das Spiel kann erst gestartet werden, wenn:
 * - mindestens zwei Spieler beigetreten sind,
 * - jeder Spieler einen Charakter gewählt hat.
 *
 * Der Server prüft diese Regeln zusätzlich verbindlich.
 *
 * @param {Object} state - Öffentlicher Spielzustand.
 */
function renderStartAvailability(state) {
    const enoughPlayers =
        state.players.length >= 2;

    const allPlayersHaveCharacter =
        state.players.every(
            player =>
                player.character !== null
        );

    startGameButton.disabled =
        !enoughPlayers
        || !allPlayersHaveCharacter
        || state.started;
}


/**
 * Rendert den öffentlichen Zustand der Lobby.
 *
 * Dabei werden insbesondere die Spielerliste,
 * die Charakterbelegung und die Startmöglichkeit
 * des Hosts aktualisiert.
 *
 * Sobald der Server meldet, dass das Spiel gestartet wurde,
 * wird automatisch zur Spielansicht gewechselt.
 *
 * @param {Object} state - Öffentlicher Spielzustand.
 */
function renderGameState(state) {
    // Sobald das Spiel gestartet wurde,
    // hat die Lobby ihren Zweck erfüllt.
    if (state.started) {
        openGame();
        return;
    }


    renderPlayers(
        state.players
    );

    renderCharacterSelection(
        state
    );

    renderStartAvailability(
        state
    );


    if (state.finished) {
        const winnerNumber =
            state.winner_index !== null
                ? state.winner_index + 1
                : "?";

        gameStatus.textContent =
            `Spiel beendet. Gewinner: Spieler ${winnerNumber}.`;

        startSection.hidden = true;

        characterSelect.disabled = true;
        selectCharacterButton.disabled = true;

        return;
    }


    gameStatus.textContent =
        "Warten auf Spielstart.";


    // Nur Spieler 0 ist Host und erhält
    // den Bereich zum Starten des Spiels.
    startSection.hidden =
        playerIndex !== 0;
}

// =============================================================================
// 4. REST- und WebSocket-Kommunikation
// =============================================================================

/**
 * Lädt den aktuellen öffentlichen Zustand des Spiels einmalig
 * über die REST-API.
 *
 * Dadurch ist die Lobby auch dann sofort korrekt dargestellt,
 * wenn die erste WebSocket-Nachricht noch nicht eingetroffen ist.
 */
async function loadInitialGameState() {
    try {
        const state = await requestJson(
            `/games/${gameId}`
        );

        renderGameState(
            state
        );

    } catch (error) {
        showError(
            error.message
        );
    }
}


/**
 * Verarbeitet eine einzelne vom Server empfangene
 * WebSocket-Nachricht.
 *
 * game_state enthält den gemeinsamen öffentlichen Zustand.
 * player_state enthält die privaten Informationen des
 * aktuell verbundenen Spielers.
 *
 * @param {Object} message - Bereits geparste WebSocket-Nachricht.
 */
function handleWebSocketMessage(message) {
    if (message.type === "game_state") {
        renderGameState(
            message.data
        );

    } else if (
        message.type === "error"
    ) {
        showError(
            message.message
        );
    }
}


/**
 * Baut die WebSocket-Verbindung zur aktuellen Lobby auf.
 *
 * Über diese Verbindung werden Änderungen wie:
 * - neue Spieler,
 * - Charakterauswahlen,
 * - der Spielstart
 *
 * ohne Seitenreload an alle verbundenen Clients übertragen.
 */
function connectWebSocket() {
    const websocketProtocol =
        window.location.protocol === "https:"
            ? "wss:"
            : "ws:";

    const websocketUrl =
        `${websocketProtocol}//`
        + `${window.location.host}`
        + `/ws/games/${gameId}`
        + `/players/${playerIndex}`;

    websocket = new WebSocket(
        websocketUrl
    );


    websocket.addEventListener(
        "open",
        () => {
            connectionStatus.textContent =
                "verbunden";
        }
    );


    websocket.addEventListener(
        "close",
        event => {
            connectionStatus.textContent =
                "getrennt";

            console.error(
                "WebSocket geschlossen:",
                event.code,
                event.reason
            );
        }
    );


    websocket.addEventListener(
        "error",
        event => {
            connectionStatus.textContent =
                "Fehler";

            console.error(
                "WebSocket-Fehler:",
                event
            );
        }
    );


    websocket.addEventListener(
        "message",
        event => {
            try {
                const message = JSON.parse(
                    event.data
                );

                handleWebSocketMessage(
                    message
                );

            } catch (error) {
                console.error(
                    "Ungültige WebSocket-Nachricht:",
                    error
                );
            }
        }
    );
}


// =============================================================================
// 5. Spielstart und Benutzeraktionen
// =============================================================================

/**
 * Übermittelt die vom aktuellen Spieler gewählte
 * Charakterklasse an den Server.
 *
 * Der Server prüft verbindlich, ob:
 * - das Spiel noch nicht gestartet wurde,
 * - der Spieler existiert,
 * - der Charakter noch nicht von einem anderen
 *   Spieler vergeben wurde.
 */
async function handleSelectCharacter() {
    clearError();

    const character =
        characterSelect.value;


    if (!character) {
        showError(
            "Bitte wähle einen Charakter."
        );

        return;
    }


    // Während des Requests weitere Klicks verhindern.
    selectCharacterButton.disabled = true;


    try {
        await requestJson(
            `/games/${gameId}`
            + `/players/${playerIndex}`
            + `/character`,
            {
                method: "PUT",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    character: character
                })
            }
        );

        /*
         * Der Endpunkt veröffentlicht anschließend den
         * aktualisierten Spielzustand über WebSocket.
         *
         * Dadurch werden sowohl dieser Client als auch
         * alle anderen Lobby-Clients automatisch aktualisiert.
         */

    } catch (error) {
        showError(
            error.message
        );

        /*
         * Falls die Auswahl beispielsweise zwischenzeitlich
         * durch einen anderen Spieler belegt wurde, laden wir
         * den aktuellen Serverzustand erneut.
         */
        await loadInitialGameState();

    } finally {
        /*
         * Solange das Spiel noch nicht gestartet wurde,
         * darf erneut gewählt werden.
         *
         * Der nächste empfangene game_state setzt den
         * endgültigen Zustand des Buttons ohnehin erneut.
         */
        selectCharacterButton.disabled = false;
    }
}

async function copyGameId() {
    try {
        await navigator.clipboard.writeText(
            gameId
        );

        copyGameIdStatus.textContent =
            "Spiel-ID kopiert.";

    } catch (error) {
        gameIdElement.select();

        document.execCommand(
            "copy"
        );

        copyGameIdStatus.textContent =
            "Spiel-ID kopiert.";
    }


    setTimeout(
        () => {
            copyGameIdStatus.textContent =
                "";
        },
        1800
    );
}

/**
 * Startet das Spiel mit der in der Lobby gewählten
 * Anzahl persönlicher Zielkarten.
 *
 * Nur Spieler 0 besitzt im Frontend die entsprechende
 * Startmöglichkeit.
 *
 * Der Server prüft zusätzlich, ob:
 * - mindestens zwei Spieler vorhanden sind,
 * - alle Spieler einen Charakter gewählt haben.
 *
 * @param {SubmitEvent} event - Submit-Event des Startformulars.
 */
async function handleStartGame(event) {
    event.preventDefault();

    clearError();

    const targetsPerPlayer = Number(
        targetsPerPlayerInput.value
    );


    if (
        !Number.isInteger(targetsPerPlayer)
        || targetsPerPlayer < 1
    ) {
        showError(
            "Die Anzahl der Zielkarten muss mindestens 1 betragen."
        );

        return;
    }


    try {
        const result = await requestJson(
            `/games/${gameId}/start`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    targets_per_player:
                        targetsPerPlayer
                })
            }
        );


        /*
         * Der startende Spieler wird direkt weitergeleitet.
         *
         * Die übrigen Spieler erhalten den neuen Zustand über
         * ihren WebSocket und werden dadurch ebenfalls automatisch
         * zur Spielansicht weitergeleitet.
         */
        if (result.started) {
            openGame();
        }

    } catch (error) {
        showError(
            error.message
        );
    }
}


/**
 * Registriert die festen Event-Listener der Lobby.
 */
/**
 * Registriert die festen Event-Listener der Lobby.
 */
function registerEventListeners() {
    // Beschreibung aktualisieren, wenn im
    // Auswahlfeld ein anderer Charakter gewählt wird.
    characterSelect.addEventListener(
        "change",
        renderCharacterDescription
    );

    // Gewählten Charakter tatsächlich
    // auf dem Server speichern.
    selectCharacterButton.addEventListener(
        "click",
        handleSelectCharacter
    );

    // Spielstart durch den Host.
    startGameForm.addEventListener(
        "submit",
        handleStartGame
    );

    copyGameIdButton.addEventListener(
    "click",
    copyGameId
);
}


// =============================================================================
// 6. Initialisierung
// =============================================================================

/**
 * Initialisiert die Lobbyseite.
 *
 * Dabei werden:
 * - Spiel-ID und Spielerindex angezeigt,
 * - die Charakterbeschreibung initialisiert,
 * - die Event-Listener registriert,
 * - die WebSocket-Verbindung aufgebaut,
 * - der aktuelle Lobbyzustand einmalig per REST geladen.
 */
function initializeLobbyPage() {
    gameIdElement.value =
        gameId;

    playerIndexElement.textContent =
        playerIndex;


    // Standardbeschreibung für die Charakterauswahl.
    renderCharacterDescription();


    // Standardmäßig nur für Spieler 0 sichtbar.
    // Der aktuelle Serverzustand entscheidet anschließend
    // endgültig über die Sichtbarkeit und Verfügbarkeit.
    startSection.hidden =
        playerIndex !== 0;

    // Bis der erste Serverzustand geladen wurde,
    // darf noch kein Spiel gestartet werden.
    startGameButton.disabled = true;


    registerEventListeners();

    connectWebSocket();

    loadInitialGameState();
}


initializeLobbyPage();