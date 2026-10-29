from app.game.enums import Direction, RotationDirection
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
        events = []

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
            game = game_manager.get_game(
                game_id
            )

            player = game.players[
                player_index
            ]


            # Zustand vor der Bewegung merken.
            previous_target = (
                player.get_current_target()
            )

            previous_keys = set(
                game.activated_keys
            )

            requested_position = (
                message.get("row"),
                message.get("column")
            )


            # Bewegung einschließlich Target-, Schlüssel-
            # und Portalverarbeitung durchführen.
            _handle_move(
                game_id,
                player_index,
                message
            )


            # -------------------------------------------------
            # Persönliches Ziel gefunden
            # -------------------------------------------------

            current_target = (
                player.get_current_target()
            )

            if (
                previous_target is not None
                and current_target
                != previous_target
            ):
                events.append(
                    {
                        "event":
                            "target_completed",
                        "target":
                            previous_target.value
                    }
                )


            # -------------------------------------------------
            # Schlüssel aktiviert
            # -------------------------------------------------

            activated_keys = (
                game.activated_keys
                - previous_keys
            )

            for key in activated_keys:
                events.append(
                    {
                        "event":
                            "key_activated",
                        "key":
                            key.value
                    }
                )


            # -------------------------------------------------
            # Portal benutzt
            # -------------------------------------------------

            actual_position = (
                player.row,
                player.column
            )

            if (
                actual_position
                != requested_position
            ):
                events.append(
                    {
                        "event":
                            "portal_used"
                    }
                )


        elif action_type == "use_magician_ability":
            _handle_magician_ability(
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
                "message":
                    "Unbekannter Nachrichtentyp."
            }


        # Nach jeder erfolgreichen Spielaktion
        # den neuen Zustand verteilen.
        await publish_game_state(
            game_id
        )


        response = {
            "type": "action_success",
            "action": action_type
        }


        # Nur hinzufügen, wenn tatsächlich
        # ein besonderes Spielereignis auftrat.
        if events:
            response["events"] = events


        return response

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

def _handle_magician_ability(
    game_id: str,
    player_index: int,
    message: dict
) -> None:
    """
    Verarbeitet die aktive Fähigkeit des Magiers.

    :param game_id: ID des Spiels.
    :param player_index: Index des Spielers.
    :param message: Empfangene WebSocket-Nachricht.
    :raises ValueError: Wenn Positionsdaten fehlen oder ungültig sind.
    """

    if "row" not in message:
        raise ValueError(
            "Für die Magier-Fähigkeit fehlt die Zeile."
        )

    if "column" not in message:
        raise ValueError(
            "Für die Magier-Fähigkeit fehlt die Spalte."
        )

    if "direction" not in message:
        raise ValueError(
            "Für die Magier-Fähigkeit fehlt die Drehrichtung."
        )

    row = message["row"]
    column = message["column"]
    try:
        direction = RotationDirection(
            message["direction"]
        )
    except ValueError:
        raise ValueError(
            "Ungültige Drehrichtung."
        )

    if (
        not isinstance(row, int)
        or not isinstance(column, int)
    ):
        raise ValueError(
            "Zeile und Spalte müssen Ganzzahlen sein."
        )

    game_manager.use_magician_ability(
        game_id,
        player_index,
        row,
        column,
        direction
    )
