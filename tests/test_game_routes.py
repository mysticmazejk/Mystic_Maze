import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.state import (
    connection_manager,
    game_manager,
)


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_application_state():
    """
    Setzt den globalen Anwendungszustand vor und nach jedem Test zurück.

    Dadurch beeinflussen sich die API-Tests nicht gegenseitig.
    """

    game_manager.games.clear()
    connection_manager.connections.clear()

    yield

    game_manager.games.clear()
    connection_manager.connections.clear()


def test_create_game():
    """
    Prüft, ob über die API ein neues Spiel erstellt werden kann.
    """

    response = client.post(
        "/games"
    )

    assert response.status_code == 200

    data = response.json()

    assert "game_id" in data
    assert len(data["game_id"]) == 6

    assert (
        data["game_id"]
        in game_manager.games
    )


def test_join_game():
    """
    Prüft, ob ein Spieler einem vorhandenen Spiel
    über die API beitreten kann.
    """

    create_response = client.post(
        "/games"
    )

    game_id = (
        create_response.json()["game_id"]
    )

    response = client.post(
        f"/games/{game_id}/players",
        json={
            "name": "Spieler 1"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["game_id"] == game_id
    assert data["player_index"] == 0
    assert data["name"] == "Spieler 1"


def test_second_player_receives_index_one():
    """
    Prüft, ob der zweite Spieler den Index 1 erhält.
    """

    game_id = (
        client.post("/games")
        .json()["game_id"]
    )

    client.post(
        f"/games/{game_id}/players",
        json={
            "name": "Spieler 1"
        }
    )

    response = client.post(
        f"/games/{game_id}/players",
        json={
            "name": "Spieler 2"
        }
    )

    assert response.status_code == 200
    assert response.json()["player_index"] == 1


def test_join_game_trims_player_name():
    """
    Prüft, ob Leerzeichen im Spielernamen
    beim Beitritt entfernt werden.
    """

    game_id = (
        client.post("/games")
        .json()["game_id"]
    )

    response = client.post(
        f"/games/{game_id}/players",
        json={
            "name": "  Spieler 1  "
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Spieler 1"


def test_duplicate_player_name_is_rejected():
    """
    Prüft, ob doppelte Spielernamen über die API
    abgelehnt werden.
    """

    game_id = (
        client.post("/games")
        .json()["game_id"]
    )

    client.post(
        f"/games/{game_id}/players",
        json={
            "name": "Noah"
        }
    )

    response = client.post(
        f"/games/{game_id}/players",
        json={
            "name": "NOAH"
        }
    )

    assert response.status_code == 400

    assert (
        "bereits vergeben"
        in response.json()["detail"]
    )


def test_empty_player_name_is_rejected():
    """
    Prüft, ob ein leerer Spielername
    über die API abgelehnt wird.
    """

    game_id = (
        client.post("/games")
        .json()["game_id"]
    )

    response = client.post(
        f"/games/{game_id}/players",
        json={
            "name": "   "
        }
    )

    assert response.status_code == 400

    assert (
        "nicht leer"
        in response.json()["detail"]
    )


def test_get_lobby_state():
    """
    Prüft, ob der öffentliche Zustand
    eines Spiels abgerufen werden kann.
    """

    game_id = (
        client.post("/games")
        .json()["game_id"]
    )

    client.post(
        f"/games/{game_id}/players",
        json={
            "name": "Spieler 1"
        }
    )

    client.post(
        f"/games/{game_id}/players",
        json={
            "name": "Spieler 2"
        }
    )

    response = client.get(
        f"/games/{game_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["game_id"] == game_id
    assert data["started"] is False
    assert data["finished"] is False

    assert len(data["players"]) == 2

    assert (
        data["players"][0]["name"]
        == "Spieler 1"
    )

    assert (
        data["players"][1]["name"]
        == "Spieler 2"
    )


def test_public_state_contains_board():
    """
    Prüft, ob der öffentliche Spielzustand
    das vollständige Board enthält.
    """

    game_id = (
        client.post("/games")
        .json()["game_id"]
    )

    response = client.get(
        f"/games/{game_id}"
    )

    assert response.status_code == 200
    print(response.json())

    board = response.json()["board"]

    assert len(board["tiles"]) == 7

    for row in board["tiles"]:
        assert len(row) == 7

    assert board["spare_tile"] is not None
    assert "allowed_shifts" in board


def test_start_game():
    """
    Prüft, ob ein Spiel mit zwei Spielern
    über die API gestartet werden kann.
    """

    game_id = (
        client.post("/games")
        .json()["game_id"]
    )

    client.post(
        f"/games/{game_id}/players",
        json={
            "name": "Spieler 1"
        }
    )

    client.post(
        f"/games/{game_id}/players",
        json={
            "name": "Spieler 2"
        }
    )

    response = client.post(
        f"/games/{game_id}/start",
        json={
            "targets_per_player": 3
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["started"] is True
    assert data["current_player_index"] == 0

    game = game_manager.get_game(
        game_id
    )

    assert len(
        game.players[0].targets
    ) == 3

    assert len(
        game.players[1].targets
    ) == 3


def test_game_cannot_start_with_one_player():
    """
    Prüft, ob ein Spiel mit nur einem Spieler
    nicht gestartet werden kann.
    """

    game_id = (
        client.post("/games")
        .json()["game_id"]
    )

    client.post(
        f"/games/{game_id}/players",
        json={
            "name": "Spieler 1"
        }
    )

    response = client.post(
        f"/games/{game_id}/start",
        json={
            "targets_per_player": 3
        }
    )

    assert response.status_code == 400

    assert (
        "mindestens zwei Spieler"
        in response.json()["detail"]
    )


def test_unknown_game_returns_error():
    """
    Prüft, ob beim Abruf eines unbekannten Spiels
    ein HTTP-Fehler zurückgegeben wird.
    """

    response = client.get(
        "/games/ABC123"
    )

    assert response.status_code == 404


def test_game_id_is_case_insensitive():
    """
    Prüft, ob eine Spiel-ID auch in Kleinbuchstaben
    verwendet werden kann.
    """

    game_id = (
        client.post("/games")
        .json()["game_id"]
    )

    response = client.get(
        f"/games/{game_id.lower()}"
    )

    assert response.status_code == 200

    assert (
        response.json()["game_id"]
        == game_id
    )