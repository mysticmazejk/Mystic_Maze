from pydantic import BaseModel


class TilePublicState(BaseModel):
    """
    Öffentlich sichtbarer Zustand einer Labyrinthkachel.
    """
    tile_type: str
    rotation: int
    fixed: bool
    gate: str | None
    gate_open: bool | None
    portal: bool
    target: str | None


class ShiftOptionPublicState(BaseModel):
    """
    Aktuell erlaubte Einschubaktion.
    """
    index: int
    direction: str


class BoardPublicState(BaseModel):
    """
    Öffentlich sichtbarer Zustand des Spielbretts.
    """
    tiles: list[list[TilePublicState]]
    spare_tile: TilePublicState
    allowed_shifts: list[ShiftOptionPublicState]


class PlayerPublicState(BaseModel):
    """
    Öffentlich sichtbare Informationen eines Spielers.
    """
    player_index: int
    name: str
    row: int
    column: int
    character: str | None
    completed_target_count: int

class PlayerPrivateState(BaseModel):
    """
    Nur für den jeweiligen Spieler bestimmte Informationen.
    """
    player_index: int

    character: str | None

    current_target: str | None
    remaining_target_count: int
    completed_targets: list[str]

    ability_available: bool
    ability_used_for_current_target: bool

class GamePublicState(BaseModel):
    """
    Öffentlich sichtbarer Zustand eines Spiels.
    """
    game_id: str

    started: bool
    finished: bool

    current_player_index: int

    has_shifted: bool
    has_moved: bool

    winner_index: int | None

    board: BoardPublicState

    players: list[PlayerPublicState]

    reachable_positions: list[PositionPublicState]


class PositionPublicState(BaseModel):
    """
    Position eines Feldes auf dem Spielbrett.
    """
    row: int
    column: int