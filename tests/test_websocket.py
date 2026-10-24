import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.state import (
    connection_manager,
    game_manager,
)


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_application_state():
    """
    Setzt Spiele und WebSocket-Verbindungen
    vor und nach jedem Test zurück.
    """

    game_manager.games.clear()
    connection_manager.connections.clear()

    yield

    game_manager.games.clear()
    connection_manager.connections.clear()


def create_started_game() -> str:
    """
    Erstellt über die API ein gestartetes Spiel
    mit zwei Spielern.

    :return: ID des erzeugten Spiels.
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

    return game_id


def receive_initial_state(websocket):
    """
    Liest die beiden Nachrichten, die beim Aufbau
    einer WebSocket-Verbindung gesendet werden.

    :param websocket: Geöffnete Test-WebSocket-Verbindung.
    :return: Tuple aus öffentlichem und privatem Zustand.
    """

    game_state = websocket.receive_json()
    player_state = websocket.receive_json()

    assert game_state["type"] == "game_state"
    assert player_state["type"] == "player_state"

    return game_state, player_state


def test_websocket_connects_to_game():
    """
    Prüft, ob sich ein vorhandener Spieler
    per WebSocket verbinden kann.
    """

    game_id = create_started_game()

    with client.websocket_connect(
        f"/ws/games/{game_id}/players/0"
    ) as websocket:

        game_state, player_state = (
            receive_initial_state(
                websocket
            )
        )

        assert (
            game_state["data"]["game_id"]
            == game_id
        )

        assert (
            player_state["data"]["player_index"]
            == 0
        )


def test_websocket_rejects_unknown_player():
    """
    Prüft, ob eine Verbindung mit einem
    unbekannten Spielerindex abgelehnt wird.
    """

    game_id = create_started_game()

    with pytest.raises(
        WebSocketDisconnect
    ):
        with client.websocket_connect(
            f"/ws/games/{game_id}/players/99"
        ):
            pass


def test_websocket_ping():
    """
    Prüft die grundlegende Kommunikation
    über die WebSocket-Verbindung.
    """

    game_id = create_started_game()

    with client.websocket_connect(
        f"/ws/games/{game_id}/players/0"
    ) as websocket:

        receive_initial_state(
            websocket
        )

        websocket.send_json(
            {
                "type": "ping"
            }
        )

        response = (
            websocket.receive_json()
        )

        assert response == {
            "type": "pong"
        }


def test_private_target_is_not_in_public_state():
    """
    Prüft, ob das persönliche Target eines Spielers
    nicht im öffentlichen Spielerzustand enthalten ist.
    """

    game_id = create_started_game()

    with client.websocket_connect(
        f"/ws/games/{game_id}/players/0"
    ) as websocket:

        game_state, player_state = (
            receive_initial_state(
                websocket
            )
        )

        public_data = game_state["data"]
        private_data = player_state["data"]

        assert (
            "current_target"
            not in public_data
        )

        for player in public_data["players"]:
            assert "current_target" not in player
            assert "targets" not in player

        assert (
            "current_target"
            in private_data
        )


def test_current_player_can_rotate_spare_tile():
    """
    Prüft, ob der aktuell aktive Spieler das
    freie Plättchen über WebSocket drehen kann.
    """

    game_id = create_started_game()

    game = game_manager.get_game(
        game_id
    )

    old_rotation = (
        game.board.spare_tile.rotation
    )

    with client.websocket_connect(
        f"/ws/games/{game_id}/players/0"
    ) as websocket:

        receive_initial_state(
            websocket
        )

        websocket.send_json(
            {
                "type": "rotate_spare_tile"
            }
        )

        game_state = (
            websocket.receive_json()
        )

        player_state = (
            websocket.receive_json()
        )

        success = (
            websocket.receive_json()
        )

        assert game_state["type"] == "game_state"
        assert player_state["type"] == "player_state"

        assert success == {
            "type": "action_success",
            "action": "rotate_spare_tile"
        }

        assert (
            game.board.spare_tile.rotation
            == (old_rotation + 1) % 4
        )


def test_inactive_player_cannot_rotate_spare_tile():
    """
    Prüft, ob ein nicht aktiver Spieler keine
    Spielaktion ausführen kann.
    """

    game_id = create_started_game()

    # Spieler 0 beginnt.
    # Spieler 1 darf daher nicht drehen.
    with client.websocket_connect(
        f"/ws/games/{game_id}/players/1"
    ) as websocket:

        receive_initial_state(
            websocket
        )

        websocket.send_json(
            {
                "type": "rotate_spare_tile"
            }
        )

        response = (
            websocket.receive_json()
        )

        assert response["type"] == "error"

        assert (
            "nicht am Zug"
            in response["message"]
        )


def test_current_player_can_shift_board():
    """
    Prüft, ob der aktive Spieler das Labyrinth
    über WebSocket verschieben kann.
    """

    game_id = create_started_game()

    with client.websocket_connect(
        f"/ws/games/{game_id}/players/0"
    ) as websocket:

        receive_initial_state(
            websocket
        )

        websocket.send_json(
            {
                "type": "shift",
                "index": 1,
                "direction": "east"
            }
        )

        game_state = (
            websocket.receive_json()
        )

        player_state = (
            websocket.receive_json()
        )

        success = (
            websocket.receive_json()
        )

        assert game_state["type"] == "game_state"
        assert player_state["type"] == "player_state"

        assert (
            game_state["data"]["has_shifted"]
            is True
        )

        assert (
            game_state["data"]["board"]["allowed_shifts"]
            == []
        )

        assert success == {
            "type": "action_success",
            "action": "shift"
        }


def test_shift_makes_reachable_positions_available():
    """
    Prüft, ob nach dem Verschieben erreichbare
    Felder an den Client übertragen werden.
    """

    game_id = create_started_game()

    with client.websocket_connect(
        f"/ws/games/{game_id}/players/0"
    ) as websocket:

        receive_initial_state(
            websocket
        )

        websocket.send_json(
            {
                "type": "shift",
                "index": 1,
                "direction": "east"
            }
        )

        game_state = (
            websocket.receive_json()
        )

        websocket.receive_json()
        websocket.receive_json()

        reachable_positions = (
            game_state["data"][
                "reachable_positions"
            ]
        )

        # Mindestens die eigene Position ist
        # immer erreichbar.
        assert len(
            reachable_positions
        ) >= 1


def test_player_can_move_to_reachable_position():
    """
    Prüft eine vollständige Schiebe- und
    Bewegungsaktion über WebSocket.
    """

    game_id = create_started_game()

    with client.websocket_connect(
        f"/ws/games/{game_id}/players/0"
    ) as websocket:

        receive_initial_state(
            websocket
        )

        # Zuerst schieben.
        websocket.send_json(
            {
                "type": "shift",
                "index": 1,
                "direction": "east"
            }
        )

        shifted_state = (
            websocket.receive_json()
        )

        # player_state
        websocket.receive_json()

        # action_success
        websocket.receive_json()

        reachable_positions = (
            shifted_state["data"][
                "reachable_positions"
            ]
        )

        assert reachable_positions

        target = reachable_positions[0]

        # Danach bewegen.
        websocket.send_json(
            {
                "type": "move",
                "row": target["row"],
                "column": target["column"]
            }
        )

        moved_state = (
            websocket.receive_json()
        )

        # player_state
        websocket.receive_json()

        success = (
            websocket.receive_json()
        )

        assert moved_state["type"] == "game_state"

        assert (
            moved_state["data"]["has_moved"]
            is True
        )

        assert (
            moved_state["data"][
                "reachable_positions"
            ]
            == []
        )

        assert success == {
            "type": "action_success",
            "action": "move"
        }


def test_current_player_can_end_turn():
    """
    Prüft, ob nach dem Verschieben der Zug
    über WebSocket beendet werden kann.
    """

    game_id = create_started_game()

    with client.websocket_connect(
        f"/ws/games/{game_id}/players/0"
    ) as websocket:

        receive_initial_state(
            websocket
        )

        # Einschieben ist vor dem Zugende verpflichtend.
        websocket.send_json(
            {
                "type": "shift",
                "index": 1,
                "direction": "east"
            }
        )

        websocket.receive_json()
        websocket.receive_json()
        websocket.receive_json()

        websocket.send_json(
            {
                "type": "end_turn"
            }
        )

        game_state = (
            websocket.receive_json()
        )

        websocket.receive_json()

        success = (
            websocket.receive_json()
        )

        assert (
            game_state["data"][
                "current_player_index"
            ]
            == 1
        )

        assert (
            game_state["data"]["has_shifted"]
            is False
        )

        assert (
            game_state["data"]["has_moved"]
            is False
        )

        assert success == {
            "type": "action_success",
            "action": "end_turn"
        }


def test_unknown_websocket_action_returns_error():
    """
    Prüft, ob unbekannte Nachrichtentypen
    abgelehnt werden.
    """

    game_id = create_started_game()

    with client.websocket_connect(
        f"/ws/games/{game_id}/players/0"
    ) as websocket:

        receive_initial_state(
            websocket
        )

        websocket.send_json(
            {
                "type": "do_something_random"
            }
        )

        response = (
            websocket.receive_json()
        )

        assert response["type"] == "error"

        assert (
            "Unbekannter Nachrichtentyp"
            in response["message"]
        )