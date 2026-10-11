from app.game.enums import Direction, TileType
from app.game.tile import Tile


def test_corner_default_openings():
    """
    Prüft die offenen Richtungen eines Eck-Plättchens
    in der Ausgangsrotation.
    """
    tile = Tile(TileType.CORNER)

    assert tile.get_openings() == {
        Direction.NORTH,
        Direction.EAST,
    }


def test_corner_rotation():
    """
    Prüft, ob sich die offenen Richtungen eines Eck-Plättchens
    nach einer Drehung korrekt verändern.
    """
    tile = Tile(TileType.CORNER)

    tile.rotate_clockwise()

    assert tile.rotation == 1
    assert tile.get_openings() == {
        Direction.EAST,
        Direction.SOUTH,
    }


def test_rotation_wraps_after_four_turns():
    """
    Prüft, ob die Rotation nach vier Drehungen
    wieder bei 0 beginnt.
    """
    tile = Tile(TileType.CORNER)

    for _ in range(4):
        tile.rotate_clockwise()

    assert tile.rotation == 0


def test_fixed_tile_does_not_rotate():
    """
    Prüft, ob eine feste Kachel nicht gedreht werden kann.
    """
    tile = Tile(
        TileType.CORNER,
        fixed=True
    )

    tile.rotate_clockwise()

    assert tile.rotation == 0


def test_cross_is_open_in_all_directions():
    """
    Prüft, ob eine Viererkreuzung in alle Richtungen geöffnet ist.
    """
    tile = Tile(TileType.CROSS)

    assert tile.get_openings() == {
        Direction.NORTH,
        Direction.EAST,
        Direction.SOUTH,
        Direction.WEST,
    }


def test_cross_openings_do_not_change_after_rotation():
    """
    Prüft, ob eine Viererkreuzung unabhängig von der Rotation
    immer in alle vier Richtungen geöffnet bleibt.
    """
    tile = Tile(TileType.CROSS)

    tile.rotate_clockwise()

    assert tile.get_openings() == {
        Direction.NORTH,
        Direction.EAST,
        Direction.SOUTH,
        Direction.WEST,
    }