from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.game_schemas import GamePublicState
from app.state import game_manager
from app.realtime import publish_game_state

router = APIRouter(
    prefix="/games",
    tags=["games"]
)


class JoinGameRequest(BaseModel):
    """
    Daten zum Beitritt zu einem Spiel.
    """
    name: str


class StartGameRequest(BaseModel):
    """
    Daten zum Starten eines Spiels.
    """
    targets_per_player: int


@router.post("")
def create_game():
    """
    Erstellt einen neuen Spielraum.
    """
    game_id = game_manager.create_game()

    return {
        "game_id": game_id
    }


@router.post("/{game_id}/players")
async def join_game(
    game_id: str,
    request: JoinGameRequest
):
    """
    Fügt einen Spieler einem bestehenden Spiel hinzu.
    """
    try:
        player_index = game_manager.add_player(
            game_id,
            request.name
        )

        player = game_manager.get_player(
            game_id,
            player_index
        )

        # Bereits verbundene Clients über die
        # neue Lobby-Zusammensetzung informieren.
        await publish_game_state(
            game_id
        )

        return {
            "game_id": game_id.upper(),
            "player_index": player_index,
            "name": player.name
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get("/{game_id}")
def get_game(
    game_id: str
):
    """
    Gibt den aktuellen Lobby- bzw. Spielstatus zurück.
    """
    try:
        game = game_manager.get_game(
            game_id
        )

        players = [
            {
                "player_index": index,
                "name": player.name
            }
            for index, player in enumerate(
                game.players
            )
        ]

        return {
            "game_id": game_id.upper(),
            "started": game.started,
            "finished": game.finished,
            "players": players
        }

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )


@router.post("/{game_id}/start")
async def start_game(
    game_id: str,
    request: StartGameRequest
):
    """
    Startet ein vorhandenes Spiel.
    """
    try:
        game_manager.start_game(
            game_id,
            request.targets_per_player
        )

        game = game_manager.get_game(
            game_id
        )

        # Alle Clients erhalten den neuen öffentlichen Zustand
        # und jeweils ihre persönlichen Zielinformationen.
        await publish_game_state(
            game_id
        )

        return {
            "game_id": game_id.upper(),
            "started": game.started,
            "current_player_index": (
                game.current_player_id
            )
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

@router.get(
    "/{game_id}",
    response_model=GamePublicState
)
def get_game(
    game_id: str
):
    """
    Gibt den öffentlich sichtbaren Spielzustand zurück.
    """
    try:
        return game_manager.get_public_game_state(
            game_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )