// =============================================================================
// 1. Seitenparameter und Elemente
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


// Allgemeine Anzeigeelemente.
const gameIdElement = document.getElementById(
    "game-id"
);

const connectionStatus = document.getElementById(
    "connection-status"
);

const turnStatus = document.getElementById(
    "turn-status"
);

const errorMessage = document.getElementById(
    "error-message"
);


// Spielfeld und Spielerinformationen.
const boardElement = document.getElementById(
    "board"
);

const spareTileElement = document.getElementById(
    "spare-tile"
);

const playerListElement = document.getElementById(
    "player-list"
);

const currentTargetElement = document.getElementById(
    "current-target"
);


// Charakter und Charakterfähigkeit.
const characterNameElement = document.getElementById(
    "character-name"
);

const abilityStatusElement = document.getElementById(
    "ability-status"
);

const magicianAbilityButton = document.getElementById(
    "magician-ability-button"
);


// Zugstatus und Bedienelemente.
const shiftStatusElement = document.getElementById(
    "shift-status"
);

const moveStatusElement = document.getElementById(
    "move-status"
);

const shiftControlsElement = document.getElementById(
    "shift-controls"
);

const rotateSpareButton = document.getElementById(
    "rotate-spare-button"
);

const endTurnButton = document.getElementById(
    "end-turn-button"
);


// Aktive WebSocket-Verbindung.
// Sie wird erst beim Initialisieren aufgebaut.
let websocket = null;


// Zuletzt empfangene Zustände.
// Sie werden benötigt, um öffentliche und private
// Informationen gemeinsam darstellen zu können.
let latestGameState = null;
let latestPlayerState = null;


// Gibt an, ob der Magier aktuell eine Kachel
// für seine Sonderfähigkeit auswählen soll.
let magicianSelectionMode = false;


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
 * Führt einen HTTP-Request aus und gibt die JSON-Antwort zurück.
 *
 * Bei einer fehlerhaften HTTP-Antwort wird eine Exception mit der vom
 * Backend gelieferten Fehlermeldung ausgelöst.
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
 * Sendet eine Spielaktion über die aktive
 * WebSocket-Verbindung an den Server.
 *
 * @param {Object} message - Zu sendende Aktion,
 *                           z. B. move, shift oder end_turn.
 */
function sendAction(message) {
    errorMessage.textContent = "";

    if (
        websocket === null
        || websocket.readyState !== WebSocket.OPEN
    ) {
        errorMessage.textContent =
            "Keine Verbindung zum Server.";

        return;
    }

    websocket.send(
        JSON.stringify(
            message
        )
    );
}


/**
 * Liefert das einfache Zeichen, mit dem ein Kacheltyp
 * aktuell dargestellt wird.
 *
 * Die Zeichen sind Platzhalter, bis später grafische
 * Waldpfade verwendet werden.
 *
 * @param {string} tileType - Typ der Kachel aus dem Serverzustand.
 * @returns {string} Zeichen für den Kacheltyp.
 */
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


/**
 * Beendet den Auswahlmodus der Magier-Fähigkeit.
 *
 * Anschließend wird das Board erneut dargestellt,
 * damit spezielle Hervorhebungen entfernt werden.
 */
function cancelMagicianSelection() {
    magicianSelectionMode = false;

    if (magicianAbilityButton !== null) {
        magicianAbilityButton.textContent =
            "Kachel drehen";
    }

    if (latestGameState !== null) {
        renderBoard(
            latestGameState
        );
    }
}


// =============================================================================
// 3. Rendering des Spielzustands
// =============================================================================

/**
 * Erstellt das Element für eine einzelne Labyrinthkachel.
 *
 * Nur der Pfad innerhalb der Kachel wird entsprechend der Rotation gedreht.
 * Targets, Tore, Portale und Spieler bleiben dadurch lesbar und aufrecht.
 *
 * Zusätzlich kann eine Board-Kachel entweder:
 * - als normales Bewegungsziel oder
 * - als Ziel der Magier-Fähigkeit
 *
 * anklickbar gemacht werden.
 *
 * @param {Object} tile - Öffentlicher Zustand der Kachel.
 * @param {number|null} [row=null] - Zeile der Kachel auf dem Board.
 * @param {number|null} [column=null] - Spalte der Kachel auf dem Board.
 * @param {Array<Object>} [reachablePositions=[]] -
 *        Aktuell erreichbare Positionen.
 * @param {boolean} [allowMovement=false] -
 *        Ob die Kachel als Bewegungsziel anklickbar sein darf.
 * @param {boolean} [allowMagicianAbility=false] -
 *        Ob die Kachel für die Magier-Fähigkeit auswählbar ist.
 * @returns {HTMLDivElement} Fertiges Element der Kachel.
 */
function createTileElement(
    tile,
    row = null,
    column = null,
    reachablePositions = [],
    allowMovement = false,
    allowMagicianAbility = false
) {
    const element = document.createElement(
        "div"
    );

    element.classList.add(
        "tile",
        `tile-${tile.tile_type}`
    );


    // Zusätzliche CSS-Klassen für besondere
    // Kacheleigenschaften.
    if (tile.fixed) {
        element.classList.add(
            "tile-fixed"
        );
    }

    if (tile.portal) {
        element.classList.add(
            "tile-portal"
        );
    }

    if (tile.gate !== null) {
        element.classList.add(
            "tile-gate"
        );

        element.classList.add(
            tile.gate_open
                ? "gate-open"
                : "gate-closed"
        );
    }


    // Der Pfad ist eine eigene Ebene,
    // damit nur dieser gedreht wird.
    const pathElement = document.createElement(
        "div"
    );

    pathElement.classList.add(
        "tile-path"
    );

    pathElement.textContent = getTileSymbol(
        tile.tile_type
    );

    pathElement.style.transform =
        `rotate(${tile.rotation * 90}deg)`;

    element.appendChild(
        pathElement
    );


    // Targets und Sonderfunktionen werden
    // unabhängig vom Pfad dargestellt.
    const overlay = document.createElement(
        "div"
    );

    overlay.classList.add(
        "tile-overlay"
    );

    if (tile.portal) {
        overlay.textContent = "🌀";

    } else if (tile.gate !== null) {
        overlay.textContent =
            tile.gate === "leaf"
                ? "🌿"
                : "🌙";

    } else if (tile.target !== null) {
        overlay.textContent = tile.target;
    }

    element.appendChild(
        overlay
    );


    // Nur echte Board-Kacheln besitzen Zeile und Spalte.
    // Das freie Plättchen wird daher weder als Bewegungsziel
    // noch als Ziel der Magier-Fähigkeit behandelt.
    if (
        row !== null
        && column !== null
    ) {
        element.dataset.row = row;
        element.dataset.column = column;


        /*
         * Magier-Auswahl besitzt Vorrang vor der normalen Bewegung.
         *
         * Dadurch führt ein Klick während des Auswahlmodus nicht
         * versehentlich zu einer Bewegung des Spielers.
         */
        if (allowMagicianAbility) {
            element.classList.add(
                "tile-magician-selectable"
            );

            element.title =
                "Diese Kachel mit der Magier-Fähigkeit drehen";

            element.addEventListener(
                "click",
                () => {
                    magicianSelectionMode = false;

                    magicianAbilityButton.textContent =
                        "Kachel drehen";

                    sendAction({
                        type: "use_magician_ability",
                        row: row,
                        column: column
                    });
                }
            );

            return element;
        }


        const reachable = reachablePositions.some(
            position =>
                position.row === row
                && position.column === column
        );

        if (
            reachable
            && allowMovement
        ) {
            element.classList.add(
                "tile-reachable"
            );

            // Ein Klick auf ein erreichbares Feld
            // sendet direkt die Bewegung.
            element.addEventListener(
                "click",
                () => {
                    sendAction({
                        type: "move",
                        row: row,
                        column: column
                    });
                }
            );
        }
    }

    return element;
}


/**
 * Rendert das vollständige 7x7-Spielbrett
 * inklusive Spielerpositionen.
 *
 * Erreichbare Felder werden nur für den aktuell
 * aktiven Spieler anklickbar.
 *
 * Während des Magier-Auswahlmodus werden stattdessen
 * sämtliche Board-Kacheln als Ziele der Fähigkeit behandelt.
 *
 * @param {Object} state - Öffentlicher Spielzustand des Servers.
 */
function renderBoard(state) {
    boardElement.innerHTML = "";

    const isMyTurn =
        state.current_player_index === playerIndex;


    const allowMagicianAbility =
        magicianSelectionMode
        && latestPlayerState !== null
        && latestPlayerState.ability_available
        && isMyTurn
        && !state.finished;


    const allowMovement =
        isMyTurn
        && state.has_shifted
        && !state.has_moved
        && !state.finished
        && !allowMagicianAbility;


    for (
        let row = 0;
        row < state.board.tiles.length;
        row++
    ) {
        for (
            let column = 0;
            column < state.board.tiles[row].length;
            column++
        ) {
            const tile =
                state.board.tiles[row][column];

            const tileElement = createTileElement(
                tile,
                row,
                column,
                state.reachable_positions,
                allowMovement,
                allowMagicianAbility
                    && !tile.fixed
            );


            // Alle Spieler bestimmen, die aktuell
            // auf dieser Kachel stehen.
            const playersHere = state.players.filter(
                player =>
                    player.row === row
                    && player.column === column
            );

            if (playersHere.length > 0) {
                const playerContainer = document.createElement(
                    "div"
                );

                playerContainer.classList.add(
                    "players-on-tile"
                );

                for (const player of playersHere) {
                    const marker = document.createElement(
                        "span"
                    );

                    marker.classList.add(
                        "player-marker"
                    );

                    // In der Oberfläche werden Spieler 1 bis 4 angezeigt,
                    // intern verwendet der Server weiterhin die Indizes 0 bis 3.
                    marker.textContent =
                        player.player_index + 1;

                    marker.title =
                        player.character !== null
                            ? `${player.name} – ${player.character}`
                            : player.name;

                    playerContainer.appendChild(
                        marker
                    );
                }

                tileElement.appendChild(
                    playerContainer
                );
            }

            boardElement.appendChild(
                tileElement
            );
        }
    }
}


/**
 * Rendert das aktuell freie Schiebeplättchen.
 *
 * @param {Object} state - Öffentlicher Spielzustand des Servers.
 */
function renderSpareTile(state) {
    spareTileElement.innerHTML = "";

    const tileElement = createTileElement(
        state.board.spare_tile
    );

    tileElement.classList.add(
        "spare-tile"
    );

    spareTileElement.appendChild(
        tileElement
    );
}


/**
 * Rendert die Liste aller Spieler mit:
 * - Name,
 * - Charakter,
 * - Zugstatus,
 * - Anzahl abgeschlossener persönlicher Ziele.
 *
 * @param {Object} state - Öffentlicher Spielzustand des Servers.
 */
function renderPlayers(state) {
    playerListElement.innerHTML = "";

    for (const player of state.players) {
        const item = document.createElement(
            "li"
        );

        let text =
            `${player.player_index + 1}: ${player.name}`;

        if (player.character !== null) {
            text +=
                ` – ${player.character}`;
        }

        if (
            player.player_index
            === state.current_player_index
        ) {
            text += " – am Zug";
        }

        if (
            player.player_index
            === playerIndex
        ) {
            text += " – Du";
        }

        text +=
            ` – ${player.completed_target_count} Ziele`;

        item.textContent = text;

        playerListElement.appendChild(
            item
        );
    }
}


/**
 * Aktualisiert die textuelle Anzeige
 * des aktuellen Zugzustands.
 *
 * @param {Object} state - Öffentlicher Spielzustand des Servers.
 */
function renderTurnState(state) {
    if (state.finished) {
        const winnerNumber =
            state.winner_index !== null
                ? state.winner_index + 1
                : "?";

        turnStatus.textContent =
            `Spiel beendet – Spieler ${winnerNumber} hat gewonnen.`;

        shiftStatusElement.textContent = "";
        moveStatusElement.textContent = "";

        return;
    }


    if (
        state.current_player_index
        === playerIndex
    ) {
        turnStatus.textContent =
            "Du bist am Zug.";

    } else {
        const currentPlayer = state.players.find(
            player =>
                player.player_index
                === state.current_player_index
        );

        turnStatus.textContent =
            `${currentPlayer?.name ?? "Ein anderer Spieler"} `
            + "ist am Zug.";
    }


    shiftStatusElement.textContent =
        state.has_shifted
            ? "Labyrinth wurde bereits verschoben."
            : "Labyrinth muss noch verschoben werden.";

    moveStatusElement.textContent =
        state.has_moved
            ? "Spieler wurde bereits bewegt."
            : "Spieler wurde noch nicht bewegt.";
}


/**
 * Rendert den privaten Zustand des angemeldeten Spielers.
 *
 * Neben dem persönlichen Ziel werden hier auch:
 * - der eigene Charakter,
 * - die Art der Fähigkeit,
 * - die aktuelle Verfügbarkeit der Fähigkeit
 *
 * dargestellt.
 *
 * @param {Object} state - Privater Spielerzustand des Servers.
 */
function renderPlayerState(state) {
    latestPlayerState = state;


    // Persönliches Ziel anzeigen.
    if (state.current_target === null) {
        currentTargetElement.textContent =
            "Alle Ziele abgeschlossen – zurück zum Startfeld!";

    } else {
        currentTargetElement.textContent =
            state.current_target;
    }


    // Gewählten Charakter darstellen.
    characterNameElement.textContent =
        state.character ?? "Kein Charakter";


    // Aktive Fähigkeit des Magiers.
    if (state.character === "Magier") {
        magicianAbilityButton.hidden = false;

        magicianAbilityButton.disabled =
            !state.ability_available;


        if (
            state.ability_used_for_current_target
        ) {
            abilityStatusElement.textContent =
                "Fähigkeit für dieses Ziel bereits verwendet.";

        } else if (
            state.ability_available
        ) {
            abilityStatusElement.textContent =
                "Fähigkeit verfügbar: "
                + "Eine Board-Kachel kann gedreht werden.";

        } else {
            abilityStatusElement.textContent =
                "Fähigkeit aktuell nicht einsetzbar.";
        }


        /*
         * Wenn der Server meldet, dass die Fähigkeit
         * nicht mehr verfügbar ist, darf kein alter
         * Auswahlmodus im Frontend bestehen bleiben.
         */
        if (!state.ability_available) {
            magicianSelectionMode = false;

            magicianAbilityButton.textContent =
                "Kachel drehen";
        }

    } else if (
        state.character === "Wächter"
    ) {
        // Die Wächter-Fähigkeit ist vollständig passiv
        // und benötigt daher keinen Aktionsbutton.
        magicianAbilityButton.hidden = true;
        magicianAbilityButton.disabled = true;

        magicianSelectionMode = false;

        abilityStatusElement.textContent =
            "Passive Fähigkeit: Geschlossene Tore "
            + "können ohne Schlüssel passiert werden.";

    } else {
        magicianAbilityButton.hidden = true;
        magicianAbilityButton.disabled = true;

        magicianSelectionMode = false;

        abilityStatusElement.textContent = "";
    }


    /*
     * Der private Zustand kann beeinflussen,
     * ob Board-Kacheln für die Magier-Fähigkeit
     * auswählbar sein dürfen.
     *
     * Deshalb wird das Board nach einem neuen
     * Player-State erneut gerendert.
     */
    if (latestGameState !== null) {
        renderBoard(
            latestGameState
        );
    }
}


/**
 * Rendert die aktuell erlaubten Einschubaktionen
 * als Pfeile um das Board.
 *
 * Die erlaubten Schiebeaktionen werden vollständig
 * vom Server vorgegeben.
 *
 * @param {Object} state - Öffentlicher Spielzustand des Servers.
 */
function renderShiftControls(state) {
    shiftControlsElement.innerHTML = "";

    const isMyTurn =
        state.current_player_index === playerIndex;

    if (
        !isMyTurn
        || state.finished
    ) {
        return;
    }

    for (const shift of state.board.allowed_shifts) {
        const button = document.createElement(
            "button"
        );

        button.type = "button";

        button.classList.add(
            "shift-button",
            `shift-${shift.direction}`
        );

        button.dataset.index =
            shift.index;


        // Symbol und Beschreibung hängen davon ab,
        // von welcher Board-Seite eingeschoben wird.
        switch (shift.direction) {
            case "east":
                button.textContent = "→";
                button.title =
                    `Reihe ${shift.index} von links einschieben`;
                break;

            case "west":
                button.textContent = "←";
                button.title =
                    `Reihe ${shift.index} von rechts einschieben`;
                break;

            case "south":
                button.textContent = "↓";
                button.title =
                    `Spalte ${shift.index} von oben einschieben`;
                break;

            case "north":
                button.textContent = "↑";
                button.title =
                    `Spalte ${shift.index} von unten einschieben`;
                break;
        }


        button.addEventListener(
            "click",
            () => {
                // Eine Schiebeaktion beendet vorsichtshalber
                // einen eventuell aktiven Magier-Auswahlmodus.
                cancelMagicianSelection();

                sendAction({
                    type: "shift",
                    index: shift.index,
                    direction: shift.direction
                });
            }
        );

        shiftControlsElement.appendChild(
            button
        );
    }
}


/**
 * Aktiviert bzw. deaktiviert die Bedienelemente
 * entsprechend dem aktuellen Zugzustand und rendert
 * die erlaubten Schiebepfeile.
 *
 * @param {Object} state - Öffentlicher Spielzustand des Servers.
 */
function renderControls(state) {
    const isMyTurn =
        state.current_player_index === playerIndex;


    // Das freie Plättchen darf nur
    // vor dem Einschieben gedreht werden.
    rotateSpareButton.disabled =
        !isMyTurn
        || state.has_shifted
        || state.finished;


    // Nach dem verpflichtenden Einschieben darf
    // der Zug beendet werden.
    // Eine Spielerbewegung ist weiterhin optional.
    endTurnButton.disabled =
        !isMyTurn
        || !state.has_shifted
        || state.finished;


    renderShiftControls(
        state
    );
}


/**
 * Rendert alle öffentlich sichtbaren Bestandteile
 * eines neuen Spielzustands.
 *
 * Diese Funktion ist der zentrale Einstiegspunkt für
 * empfangene game_state-Nachrichten sowie für den
 * initial per REST geladenen Zustand.
 *
 * @param {Object} state - Öffentlicher Spielzustand des Servers.
 */
function renderGameState(state) {
    latestGameState = state;


    /*
     * Wenn das Spiel beendet oder ein anderer Spieler
     * am Zug ist, darf kein lokaler Magier-Auswahlmodus
     * bestehen bleiben.
     */
    if (
        state.finished
        || state.current_player_index !== playerIndex
    ) {
        magicianSelectionMode = false;

        if (magicianAbilityButton !== null) {
            magicianAbilityButton.textContent =
                "Kachel drehen";
        }
    }


    renderBoard(
        state
    );

    renderSpareTile(
        state
    );

    renderPlayers(
        state
    );

    renderTurnState(
        state
    );

    renderControls(
        state
    );
}


// =============================================================================
// 4. REST- und WebSocket-Kommunikation
// =============================================================================

/**
 * Lädt den aktuellen öffentlichen Spielzustand
 * einmalig über die REST-API.
 *
 * Dadurch kann das Board bereits dargestellt werden,
 * bevor bzw. unabhängig davon, ob die erste
 * WebSocket-Nachricht eingetroffen ist.
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
        errorMessage.textContent =
            error.message;
    }
}


/**
 * Verarbeitet eine einzelne vom Server
 * empfangene WebSocket-Nachricht.
 *
 * @param {Object} message - Bereits geparste WebSocket-Nachricht.
 */
function handleWebSocketMessage(message) {
    if (
        message.type === "game_state"
    ) {
        renderGameState(
            message.data
        );

    } else if (
        message.type === "player_state"
    ) {
        renderPlayerState(
            message.data
        );

    } else if (
        message.type === "error"
    ) {
        /*
         * Bei einem Fehler der Magier-Aktion wird der lokale
         * Auswahlmodus beendet. Der Serverzustand bleibt
         * weiterhin die verbindliche Quelle.
         */
        cancelMagicianSelection();

        errorMessage.textContent =
            message.message;

    } else if (
        message.type === "action_success"
    ) {
        /*
         * Nach einer erfolgreichen Magier-Aktion soll
         * keine alte Kachelauswahl aktiv bleiben.
         */
        if (
            message.action
            === "use_magician_ability"
        ) {
            cancelMagicianSelection();
        }

        console.log(
            "Aktion erfolgreich:",
            message.action
        );
    }
}


/**
 * Baut die WebSocket-Verbindung des aktuellen Spielers
 * zum laufenden Spiel auf und registriert alle benötigten
 * Event-Handler.
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

            cancelMagicianSelection();

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
// 5. Benutzeraktionen und Initialisierung
// =============================================================================

/**
 * Schaltet den Auswahlmodus der Magier-Fähigkeit
 * ein beziehungsweise wieder aus.
 *
 * Die eigentliche Prüfung, ob die Fähigkeit verwendet
 * werden darf, erfolgt verbindlich auf dem Server.
 */
function handleMagicianAbilityButton() {
    if (
        latestPlayerState === null
        || !latestPlayerState.ability_available
    ) {
        return;
    }


    magicianSelectionMode =
        !magicianSelectionMode;


    magicianAbilityButton.textContent =
        magicianSelectionMode
            ? "Auswahl abbrechen"
            : "Kachel drehen";


    if (latestGameState !== null) {
        renderBoard(
            latestGameState
        );
    }
}


/**
 * Registriert die festen Bedienelemente der Spielansicht.
 *
 * Dynamische Elemente wie Bewegungsfelder,
 * Magier-Kacheln und Schiebepfeile erhalten ihre
 * Listener direkt beim jeweiligen Rendering.
 */
function registerEventListeners() {
    rotateSpareButton.addEventListener(
        "click",
        () => {
            cancelMagicianSelection();

            sendAction({
                type: "rotate_spare_tile"
            });
        }
    );


    endTurnButton.addEventListener(
        "click",
        () => {
            cancelMagicianSelection();

            sendAction({
                type: "end_turn"
            });
        }
    );


    magicianAbilityButton.addEventListener(
        "click",
        handleMagicianAbilityButton
    );
}


/**
 * Initialisiert die Spielansicht.
 *
 * Die REST-Abfrage liefert den aktuellen Zustand
 * für die erste Darstellung.
 *
 * Parallel sorgt der WebSocket anschließend
 * für alle Live-Aktualisierungen.
 */
function initializeGamePage() {
    gameIdElement.textContent =
        gameId;


    /*
     * Bis der erste private Player-State empfangen wurde,
     * wird die aktive Charakterfähigkeit ausgeblendet.
     */
    magicianAbilityButton.hidden = true;
    magicianAbilityButton.disabled = true;

    characterNameElement.textContent =
        "Wird geladen...";

    abilityStatusElement.textContent =
        "Wird geladen...";


    registerEventListeners();

    connectWebSocket();

    loadInitialGameState();
}


initializeGamePage();