import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.game.enums import CharacterType, Direction
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

    Dadurch kann kein Spielzustand oder eine alte Verbindung
    einen nachfolgenden Test beeinflussen.
    """
    game_manager.games.clear()
    connection_manager.connections.clear()

    yield

    game_manager.games.clear()
    connection_manager.connections.clear()


def create_started_game() -> str:
    """
    Erstellt über die REST-API ein gestartetes Spiel
    mit zwei Spielern.

    Spieler 0 erhält den Magier und Spieler 1 den Wächter,
    damit die verpflichtende Charakterauswahl vor dem
    Spielstart erfüllt ist.

    Die Charaktere werden momentan direkt über das Game-Objekt
    vergeben, solange noch kein eigener REST-Endpunkt für die
    Charakterauswahl existiert.

    :return: ID des erzeugten und gestarteten Spiels.
    """
    game_id = (
        client.post("/games")
        .json()["game_id"]
    )

    first_player_response = client.post(
        f"/games/{game_id}/players",
        json={
            "name": "Spieler 1"
        }
    )

    second_player_response = client.post(
        f"/games/{game_id}/players",
        json={
            "name": "Spieler 2"
        }
    )

    assert first_player_response.status_code == 200
    assert second_player_response.status_code == 200

    game = game_manager.get_game(
        game_id
    )

    # Pflichtauswahl der beiden verfügbaren Charaktere.
    game.select_character(
        0,
        CharacterType.MAGICIAN
    )

    game.select_character(
        1,
        CharacterType.GUARDIAN
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
    Liest die beiden Zustandsnachrichten, die nach dem Aufbau
    einer WebSocket-Verbindung an einen Spieler gesendet werden.

    Erwartet werden:
    1. der öffentliche Spielzustand,
    2. der private Zustand des verbundenen Spielers.

    :param websocket: Geöffnete Test-WebSocket-Verbindung.
    :return: Tuple aus öffentlichem Game-State und privatem Player-State.
    """
    game_state = websocket.receive_json()
    player_state = websocket.receive_json()

    assert game_state["type"] == "game_state"
    assert player_state["type"] == "player_state"

    return game_state, player_state


def test_websocket_connects_to_game():
    """
    Prüft, ob sich ein vorhandener Spieler
    per WebSocket mit seinem Spiel verbinden kann.
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
    Prüft, ob eine WebSocket-Verbindung mit einem
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
    Prüft die grundlegende bidirektionale Kommunikation
    über eine WebSocket-Verbindung.
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
    nicht im öffentlich sichtbaren Spielzustand enthalten ist.

    Der jeweils eigene Player-State darf das persönliche
    aktuelle Ziel dagegen enthalten.
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
    freie Schiebeplättchen über WebSocket drehen kann.
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

        # Nach einer erfolgreichen Aktion sendet der Server
        # zunächst den aktualisierten öffentlichen Zustand,
        # danach den privaten Player-State und abschließend
        # die Erfolgsbestätigung.
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
    Spielaktion für den aktiven Zug ausführen kann.
    """
    game_id = create_started_game()

    # Spieler 0 beginnt die Partie.
    # Spieler 1 darf daher das Spare Tile nicht drehen.
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

        # Nach dem verpflichtenden Einschieben darf im selben
        # Zug kein zweites Mal geschoben werden.
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

        # Privaten Zustand und Erfolgsbestätigung lesen,
        # damit die WebSocket-Nachrichten vollständig
        # verarbeitet sind.
        websocket.receive_json()
        websocket.receive_json()

        reachable_positions = (
            game_state["data"][
                "reachable_positions"
            ]
        )

        # Mindestens die aktuelle Position des Spielers
        # gehört immer zur erreichbaren Menge.
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

        # Zuerst wird das Labyrinth verschoben.
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

        # Für den Test genügt eine beliebige vom Server
        # als erreichbar gemeldete Position.
        target = reachable_positions[0]

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

        # Nach der Bewegung dürfen im selben Zug
        # keine weiteren Bewegungsziele angeboten werden.
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
    Prüft, ob der aktuelle Spieler seinen Zug
    nach dem verpflichtenden Einschieben beenden kann.
    """
    game_id = create_started_game()

    with client.websocket_connect(
        f"/ws/games/{game_id}/players/0"
    ) as websocket:

        receive_initial_state(
            websocket
        )

        # Ein Zug darf erst nach dem Einschieben
        # des freien Plättchens beendet werden.
        websocket.send_json(
            {
                "type": "shift",
                "index": 1,
                "direction": "east"
            }
        )

        # game_state
        websocket.receive_json()

        # player_state
        websocket.receive_json()

        # action_success
        websocket.receive_json()

        websocket.send_json(
            {
                "type": "end_turn"
            }
        )

        game_state = (
            websocket.receive_json()
        )

        # player_state
        websocket.receive_json()

        success = (
            websocket.receive_json()
        )

        # Spieler 1 ist nach dem Zugwechsel aktiv.
        assert (
            game_state["data"][
                "current_player_index"
            ]
            == 1
        )

        # Die Zugzustände werden für den neuen
        # Spieler vollständig zurückgesetzt.
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
    Prüft, ob unbekannte WebSocket-Nachrichtentypen
    mit einer Fehlermeldung abgelehnt werden.
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

def test_magician_can_rotate_movable_tile_via_websocket():
    """
    Prüft, ob der Magier seine aktive Fähigkeit
    über WebSocket einsetzen kann.
    """
    game_id = create_started_game()

    game = game_manager.get_game(
        game_id
    )

    # Spieler 0 ist in unserem Testspiel der Magier.
    player = game.players[0]

    assert (
        player.character
        == CharacterType.MAGICIAN
    )

    # Die Fähigkeit wird erst nach dem
    # normalen Einschieben verfügbar.
    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    # Bewegliche Kachel für den Test suchen.
    target_row = None
    target_column = None

    for row in range(game.board.SIZE):
        for column in range(game.board.SIZE):
            tile = game.board.tiles[row][column]

            if not tile.fixed:
                target_row = row
                target_column = column
                break

        if target_row is not None:
            break

    tile = game.board.tiles[
        target_row
    ][target_column]

    old_rotation = tile.rotation

    with client.websocket_connect(
        f"/ws/games/{game_id}/players/0"
    ) as websocket:

        receive_initial_state(
            websocket
        )

        websocket.send_json(
            {
                "type": "use_magician_ability",
                "row": target_row,
                "column": target_column
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
            "action": "use_magician_ability"
        }

        assert (
            tile.rotation
            == (old_rotation + 1) % 4
        )

        assert (
            player_state["data"][
                "ability_used_for_current_target"
            ]
            is True
        )

        assert (
            player_state["data"][
                "ability_available"
            ]
            is False
        )


def test_magician_cannot_rotate_fixed_tile_via_websocket():
    """
    Prüft, ob eine feste Kachel auch über eine
    direkte WebSocket-Anfrage nicht gedreht werden kann.

    Damit wird sichergestellt, dass die Regel nicht
    ausschließlich vom Frontend durchgesetzt wird.
    """
    game_id = create_started_game()

    game = game_manager.get_game(
        game_id
    )

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    # (2, 2) ist eine feste Kachel.
    tile = game.board.tiles[2][2]

    assert tile.fixed is True

    old_rotation = tile.rotation

    with client.websocket_connect(
        f"/ws/games/{game_id}/players/0"
    ) as websocket:

        receive_initial_state(
            websocket
        )

        websocket.send_json(
            {
                "type": "use_magician_ability",
                "row": 2,
                "column": 2
            }
        )

        response = (
            websocket.receive_json()
        )

        assert response["type"] == "error"

        assert (
            "Feste Kacheln"
            in response["message"]
        )

    assert tile.rotation == old_rotation

    assert (
        game.players[0]
        .ability_used_for_current_target
        is False
    )


def test_guardian_has_no_active_magician_ability():
    """
    Prüft, ob der Wächter im privaten Zustand
    keine aktive Magier-Fähigkeit angeboten bekommt.
    """
    game_id = create_started_game()

    game = game_manager.get_game(
        game_id
    )

    # Spieler 1 ist der Wächter.
    game.current_player_index = 1

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    state = game_manager.get_private_player_state(
        game_id,
        1
    )

    assert state.character == "Wächter"
    assert state.ability_available is False