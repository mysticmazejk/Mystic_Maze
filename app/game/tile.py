from dataclasses import dataclass

from app.game.enums import Direction, TileType, GateType
from app.game.target import Target


@dataclass
class Tile:
    tile_type: TileType
    rotation: int = 0
    fixed: bool = False
    gate: GateType | None = None
    portal: bool = False
    target: Target | None = None


    def rotate_clockwise(self) -> None:
        if not self.fixed:
            self.rotation = (self.rotation + 1) % 4

    def get_openings(self) -> set[Direction]:
        base_openings = {
            TileType.STRAIGHT: {
                Direction.NORTH,
                Direction.SOUTH,
            },
            TileType.CORNER: {
                Direction.NORTH,
                Direction.EAST,
            },
            TileType.T_JUNCTION: {
                Direction.WEST,
                Direction.NORTH,
                Direction.EAST,
            },
            TileType.CROSS: {
                Direction.NORTH,
                Direction.EAST,
                Direction.SOUTH,
                Direction.WEST,
            },
        }

        openings = base_openings[self.tile_type]

        for _ in range(self.rotation):
            openings = {
                self._rotate_direction(direction)
                for direction in openings
            }

        return openings

    @staticmethod
    def _rotate_direction(direction: Direction) -> Direction:
        directions = [
            Direction.NORTH,
            Direction.EAST,
            Direction.SOUTH,
            Direction.WEST,
        ]

        current_index = directions.index(direction)
        next_index = (current_index + 1) % 4

        return directions[next_index]