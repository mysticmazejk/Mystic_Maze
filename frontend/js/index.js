// =============================================================================
// 1. Elemente
// =============================================================================

const createGameForm = document.getElementById(
    "create-game-form"
);

const joinGameForm = document.getElementById(
    "join-game-form"
);

const createNameInput = document.getElementById(
    "create-name"
);

const joinGameIdInput = document.getElementById(
    "join-game-id"
);

const joinNameInput = document.getElementById(
    "join-name"
);

const errorMessage = document.getElementById(
    "error-message"
);


// =============================================================================
// 2. Allgemeine Hilfsfunktionen
// =============================================================================

/**
 * Führt einen HTTP-Request aus und gibt die geparste JSON-Antwort zurück.
 *
 * Bei einer fehlerhaften Antwort wird die vom Backend übermittelte
 * Fehlermeldung als Exception weitergegeben.
 *
 * @param {string} url - Ziel-URL des Requests.
 * @param {RequestInit} [options={}] - Optionen für fetch(),
 *                                     beispielsweise Methode oder Body.
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
 * Zeigt eine Fehlermeldung auf der Startseite an.
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
 * Öffnet die Lobby eines Spiels.
 *
 * Spiel-ID und Spielerindex werden als URL-Parameter übergeben,
 * damit die Lobby weiß, zu welchem Spiel und Spieler sie gehört.
 *
 * @param {string} gameId - ID des Spiels.
 * @param {number} playerIndex - Index des beigetretenen Spielers.
 */
function openLobby(
    gameId,
    playerIndex
) {
    const url = new URL(
        "/static/lobby.html",
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
// 3. Spiel erstellen
// =============================================================================

/**
 * Erstellt ein neues Spiel und fügt den Ersteller
 * direkt als ersten Spieler hinzu.
 *
 * Danach wird der Benutzer in die Lobby des neuen Spiels weitergeleitet.
 *
 * @param {SubmitEvent} event - Submit-Event des Formulars.
 */
async function handleCreateGame(event) {
    event.preventDefault();

    clearError();

    const name = createNameInput
        .value
        .trim();

    if (!name) {
        showError(
            "Bitte gib einen Spielernamen ein."
        );

        return;
    }

    try {
        // Zunächst einen neuen Spielraum erzeugen.
        const createdGame = await requestJson(
            "/games",
            {
                method: "POST"
            }
        );

        // Der Ersteller tritt dem gerade erzeugten
        // Spiel unmittelbar als erster Spieler bei.
        const joinedGame = await requestJson(
            `/games/${createdGame.game_id}/players`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: name
                })
            }
        );

        openLobby(
            joinedGame.game_id,
            joinedGame.player_index
        );

    } catch (error) {
        showError(
            error.message
        );
    }
}


// =============================================================================
// 4. Bestehendem Spiel beitreten
// =============================================================================

/**
 * Fügt einen Spieler einem bereits vorhandenen Spiel hinzu.
 *
 * Die eingegebene Spiel-ID wird vor dem Request bereinigt
 * und in Großbuchstaben umgewandelt.
 *
 * @param {SubmitEvent} event - Submit-Event des Formulars.
 */
async function handleJoinGame(event) {
    event.preventDefault();

    clearError();

    const gameId = joinGameIdInput
        .value
        .trim()
        .toUpperCase();

    const name = joinNameInput
        .value
        .trim();

    if (!gameId) {
        showError(
            "Bitte gib eine Spiel-ID ein."
        );

        return;
    }

    if (!name) {
        showError(
            "Bitte gib einen Spielernamen ein."
        );

        return;
    }

    try {
        const joinedGame = await requestJson(
            `/games/${gameId}/players`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: name
                })
            }
        );

        openLobby(
            joinedGame.game_id,
            joinedGame.player_index
        );

    } catch (error) {
        showError(
            error.message
        );
    }
}


// =============================================================================
// 5. Event-Registrierung und Initialisierung
// =============================================================================

/**
 * Registriert die Event-Listener der Startseite.
 */
function registerEventListeners() {
    createGameForm.addEventListener(
        "submit",
        handleCreateGame
    );

    joinGameForm.addEventListener(
        "submit",
        handleJoinGame
    );
}


/**
 * Initialisiert die Startseite von Mystic Maze.
 */
function initializeIndexPage() {
    registerEventListeners();
}


initializeIndexPage();