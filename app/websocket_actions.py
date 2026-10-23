from app.game.enums import Direction
from app.realtime import publish_game_state
from app.state import game_manager


async def handle_game_action(
    game_id: str,
    player_index: int,
    message: dict
) -> dict | None:
    """
    Verarbeitet eine über WebSocket empfangene Spielaktion.

    Nach einer erfolgreichen Aktion wird der aktualisierte
    Spielzustand an alle verbundenen Spieler übertragen.

    :param game_id: ID des Spiels.
    :param player_index: Index des ausführenden Spielers.
    :param message: Empfangene WebSocket-Nachricht.
    :return: Optionale direkte Antwort an den Absender.
    """

    action_type = message.get(
        "type"
    )

    try:

        if action_type == "ping":
            return {
                "type": "pong"
            }

        if action_type == "rotate_spare_tile":
            game_manager.rotate_spare_tile(
                game_id,
                player_index
            )

        elif action_type == "shift":
            _handle_shift(
                game_id,
                player_index,
                message
            )

        elif action_type == "move":
            _handle_move(
                game_id,
                player_index,
                message
            )

        elif action_type == "end_turn":
            game_manager.end_turn(
                game_id,
                player_index
            )

        else:
            return {
                "type": "error",
                "message": "Unbekannter Nachrichtentyp."
            }

        # Nach jeder erfolgreichen Spielaktion
        # den neuen Zustand verteilen.
        await publish_game_state(
            game_id
        )

        return {
            "type": "action_success",
            "action": action_type
        }

    except (
        ValueError,
        TypeError
    ) as error:

        return {
            "type": "error",
            "message": str(error)
        }


def _handle_shift(
    game_id: str,
    player_index: int,
    message: dict
) -> None:
    """
    Verarbeitet eine Schiebeaktion.

    :param game_id: ID des Spiels.
    :param player_index: Index des Spielers.
    :param message: Empfangene Nachricht.
    :raises ValueError: Wenn erforderliche Daten fehlen oder ungültig sind.
    """

    if "index" not in message:
        raise ValueError(
            "Für eine Schiebeaktion fehlt der Index."
        )

    if "direction" not in message:
        raise ValueError(
            "Für eine Schiebeaktion fehlt die Richtung."
        )

    index = message["index"]

    if not isinstance(index, int):
        raise ValueError(
            "Der Index muss eine Ganzzahl sein."
        )

    try:
        direction = Direction(
            message["direction"]
        )

    except ValueError:
        raise ValueError(
            "Ungültige Schieberichtung."
        )

    game_manager.shift_board(
        game_id,
        player_index,
        index,
        direction
    )


def _handle_move(
    game_id: str,
    player_index: int,
    message: dict
) -> None:
    """
    Verarbeitet eine Spielerbewegung.

    :param game_id: ID des Spiels.
    :param player_index: Index des Spielers.
    :param message: Empfangene Nachricht.
    :raises ValueError: Wenn erforderliche Positionsdaten fehlen.
    """

    if "row" not in message:
        raise ValueError(
            "Für eine Bewegung fehlt die Zielzeile."
        )

    if "column" not in message:
        raise ValueError(
            "Für eine Bewegung fehlt die Zielspalte."
        )

    row = message["row"]
    column = message["column"]

    if (
        not isinstance(row, int)
        or not isinstance(column, int)
    ):
        raise ValueError(
            "Zeile und Spalte müssen Ganzzahlen sein."
        )

    game_manager.move_player(
        game_id,
        player_index,
        row,
        column
    )