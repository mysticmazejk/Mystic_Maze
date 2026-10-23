from app.state import (
    connection_manager,
    game_manager,
)


async def publish_game_state(
    game_id: str
) -> None:
    """
    Sendet den aktuellen Zustand eines Spiels
    an alle verbundenen Clients.

    Der öffentliche Spielzustand wird an alle Spieler gesendet.
    Der private Spielerzustand wird jeweils nur an den
    zugehörigen Spieler gesendet.

    :param game_id: ID des Spiels.
    """

    game_id = game_id.upper()

    # Öffentlichen Zustand erzeugen.
    public_state = (
        game_manager.get_public_game_state(
            game_id
        )
    )

    await connection_manager.broadcast(
        game_id,
        {
            "type": "game_state",
            "data": public_state.model_dump(
                mode="json"
            )
        }
    )

    # Private Informationen separat an die
    # jeweiligen Spieler senden.
    game = game_manager.get_game(
        game_id
    )

    for player_index in range(
        len(game.players)
    ):
        private_state = (
            game_manager.get_private_player_state(
                game_id,
                player_index
            )
        )

        await connection_manager.send_to_player(
            game_id,
            player_index,
            {
                "type": "player_state",
                "data": private_state.model_dump(
                    mode="json"
                )
            }
        )