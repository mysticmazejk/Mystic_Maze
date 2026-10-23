from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from app.realtime import publish_game_state
from app.state import (
    connection_manager,
    game_manager,
)
from app.websocket_actions import (
    handle_game_action,
)


router = APIRouter(
    tags=["websocket"]
)


@router.websocket(
    "/ws/games/{game_id}/players/{player_index}"
)
async def game_websocket(
    websocket: WebSocket,
    game_id: str,
    player_index: int
):
    """
    Öffnet eine WebSocket-Verbindung für einen Spieler.

    :param websocket: WebSocket-Verbindung.
    :param game_id: ID des Spiels.
    :param player_index: Index des Spielers.
    """

    game_id = game_id.upper()

    # Vor der Verbindung prüfen,
    # ob Spiel und Spieler existieren.
    try:
        game_manager.get_player(
            game_id,
            player_index
        )

    except ValueError:
        await websocket.close(
            code=1008,
            reason=(
                "Spiel oder Spieler nicht gefunden."
            )
        )

        return

    await connection_manager.connect(
        game_id,
        player_index,
        websocket
    )

    try:

        # Direkt nach dem Verbinden
        # aktuellen Zustand senden.
        await publish_game_state(
            game_id
        )

        while True:

            message = (
                await websocket.receive_json()
            )

            response = (
                await handle_game_action(
                    game_id,
                    player_index,
                    message
                )
            )

            if response is not None:
                await websocket.send_json(
                    response
                )

    except WebSocketDisconnect:

        connection_manager.disconnect(
            game_id,
            player_index,
            websocket
        )