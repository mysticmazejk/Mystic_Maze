from enum import Enum

class Direction(Enum):
    NORTH = "north"
    EAST = "east"
    SOUTH = "south"
    WEST = "west"

class TileType(Enum):
    STRAIGHT = "straight"
    CORNER = "corner"
    T_JUNCTION = "t_junction"
    CROSS = "cross"

class GateType(Enum):
    LEAF = "leaf"
    MOON = "moon"

class CharacterType(Enum):
    MAGICIAN = "Magier"
    GUARDIAN = "Wächter"

class RotationDirection(Enum):
    LEFT = "left"
    RIGHT = "right"