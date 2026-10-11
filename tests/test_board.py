from app.game.board import Board
from app.game.enums import Direction, TileType
from app.game.tile import Tile
from app.game.target import Target


def test_board_has_correct_size():
    """
    Prüft, ob das Spielbrett 7x7 Felder besitzt.
    """
    board = Board()

    assert len(board.tiles) == 7

    for row in board.tiles:
        assert len(row) == 7


def test_board_contains_no_empty_fields():
    """
    Prüft, ob nach der Initialisierung jedes Feld
    mit einer Kachel belegt ist.
    """
    board = Board()

    for row in board.tiles:
        for tile in row:
            assert tile is not None


def test_board_has_16_fixed_tiles():
    """
    Prüft, ob genau 16 feste Kacheln auf dem Spielbrett liegen.
    """
    board = Board()

    fixed_tiles = [
        tile
        for row in board.tiles
        for tile in row
        if tile.fixed
    ]

    assert len(fixed_tiles) == 16


def test_board_has_spare_tile():
    """
    Prüft, ob nach der Initialisierung ein Schiebeplättchen vorhanden ist.
    """
    board = Board()

    assert board.spare_tile is not None
    assert board.spare_tile.fixed is False


def test_board_contains_two_gate_tiles_in_total():
    """
    Prüft, ob insgesamt genau zwei Tor-Kacheln existieren.

    Dabei kann sich eines der Tore auch aktuell
    außerhalb des Bretts als Schiebeplättchen befinden.
    """
    board = Board()

    gate_count = sum(
        1
        for row in board.tiles
        for tile in row
        if tile.gate
    )

    if board.spare_tile.gate:
        gate_count += 1

    assert gate_count == 2


def test_gate_tiles_are_crosses():
    """
    Prüft, ob beide Tor-Kacheln Viererkreuzungen sind.
    """
    board = Board()

    all_tiles = [
        tile
        for row in board.tiles
        for tile in row
    ]

    all_tiles.append(board.spare_tile)

    gate_tiles = [
        tile
        for tile in all_tiles
        if tile.gate
    ]

    assert len(gate_tiles) == 2

    for tile in gate_tiles:
        assert tile.tile_type == TileType.CROSS


def test_only_valid_shift_indices_are_allowed():
    """
    Prüft, ob nur die Reihen bzw. Spalten
    1, 3 und 5 verschoben werden dürfen.
    """
    board = Board()

    invalid_indices = [0, 2, 4, 6]

    for index in invalid_indices:
        try:
            board.insert_spare_tile(
                index,
                Direction.EAST
            )

            assert False, "Ungültiger Index wurde akzeptiert."

        except ValueError:
            pass


def test_shift_row_from_left():
    """
    Prüft das Einschieben einer Reihe von links.
    """
    board = Board()

    # Eine bekannte Kachel als Schiebeplättchen setzen.
    spare = Tile(TileType.CROSS, gate=True)
    board.spare_tile = spare

    # Referenz auf die Kachel ganz rechts vor dem Schieben merken.
    old_right_tile = board.tiles[1][6]

    board.insert_spare_tile(
        1,
        Direction.EAST
    )

    # Das bisherige Schiebeplättchen muss jetzt links liegen.
    assert board.tiles[1][0] is spare

    # Die vorher ganz rechte Kachel ist nun das neue Schiebeplättchen.
    assert board.spare_tile is old_right_tile


def test_can_move_between_connected_tiles():
    """
    Prüft, ob eine direkte Bewegung zwischen zwei
    passend verbundenen Kacheln möglich ist.
    """
    board = Board()

    board.tiles[1][1] = Tile(
        TileType.STRAIGHT,
        rotation=1
    )

    board.tiles[1][2] = Tile(
        TileType.STRAIGHT,
        rotation=1
    )

    assert board.can_move(
        1,
        1,
        1,
        2
    )


def test_cannot_move_between_unconnected_tiles():
    """
    Prüft, ob keine Bewegung möglich ist,
    wenn die Öffnungen zweier Nachbarkacheln nicht zusammenpassen.
    """
    board = Board()

    board.tiles[1][1] = Tile(
        TileType.STRAIGHT,
        rotation=0
    )

    board.tiles[1][2] = Tile(
        TileType.STRAIGHT,
        rotation=0
    )

    assert not board.can_move(
        1,
        1,
        1,
        2
    )


def test_cannot_move_diagonally():
    """
    Prüft, ob diagonale Bewegungen grundsätzlich nicht erlaubt sind.
    """
    board = Board()

    assert not board.can_move(
        1,
        1,
        2,
        2
    )


def test_get_reachable_positions_includes_start():
    """
    Prüft, ob die Startposition selbst als erreichbar gilt.
    """
    board = Board()

    reachable = board.get_reachable_positions(
        3,
        3
    )

    assert (3, 3) in reachable




def test_board_contains_24_targets():
    """
    Prüft, ob insgesamt genau 24 Targets auf festen und beweglichen
    Kacheln verteilt sind.
    """
    board = Board()

    all_tiles = [
        tile
        for row in board.tiles
        for tile in row
    ]

    all_tiles.append(board.spare_tile)

    target_tiles = [
        tile
        for tile in all_tiles
        if tile.target is not None
    ]

    assert len(target_tiles) == 24


def test_every_target_exists_exactly_once():
    """
    Prüft, ob jedes definierte Target genau einmal im Spiel vorkommt.
    """
    board = Board()

    all_tiles = [
        tile
        for row in board.tiles
        for tile in row
    ]

    all_tiles.append(board.spare_tile)

    found_targets = [
        tile.target
        for tile in all_tiles
        if tile.target is not None
    ]

    assert len(found_targets) == len(Target)
    assert set(found_targets) == set(Target)


def test_exactly_12_targets_are_on_fixed_tiles():
    """
    Prüft, ob genau zwölf Targets auf festen Kacheln liegen.
    """
    board = Board()

    fixed_targets = [
        tile
        for row in board.tiles
        for tile in row
        if tile.fixed and tile.target is not None
    ]

    assert len(fixed_targets) == 12


def test_exactly_12_targets_are_on_movable_tiles():
    """
    Prüft, ob genau zwölf Targets auf beweglichen Kacheln liegen.

    Das Schiebeplättchen wird dabei ebenfalls berücksichtigt.
    """
    board = Board()

    movable_targets = [
        tile
        for row in board.tiles
        for tile in row
        if not tile.fixed and tile.target is not None
    ]

    if (
        board.spare_tile is not None
        and board.spare_tile.target is not None
    ):
        movable_targets.append(board.spare_tile)

    assert len(movable_targets) == 12


def test_straight_tiles_have_no_target():
    """
    Prüft, ob gerade Kacheln niemals ein Target tragen.
    """
    board = Board()

    all_tiles = [
        tile
        for row in board.tiles
        for tile in row
    ]

    all_tiles.append(board.spare_tile)

    for tile in all_tiles:
        if tile.tile_type == TileType.STRAIGHT:
            assert tile.target is None


def test_gate_tiles_have_no_target():
    """
    Prüft, ob Tor-Kacheln niemals ein Target tragen.
    """
    board = Board()

    all_tiles = [
        tile
        for row in board.tiles
        for tile in row
    ]

    all_tiles.append(board.spare_tile)

    gate_tiles = [
        tile
        for tile in all_tiles
        if tile.gate
    ]

    assert len(gate_tiles) == 2

    for tile in gate_tiles:
        assert tile.target is None


def test_portal_tiles_have_no_target():
    """
    Prüft, ob Portal-Kacheln niemals ein Target tragen.
    """
    board = Board()

    all_tiles = [
        tile
        for row in board.tiles
        for tile in row
    ]

    all_tiles.append(board.spare_tile)

    portal_tiles = [
        tile
        for tile in all_tiles
        if tile.portal
    ]

    assert len(portal_tiles) == 2

    for tile in portal_tiles:
        assert tile.target is None


def test_portal_tiles_are_corners():
    """
    Prüft, ob beide Portal-Kacheln Eckkacheln sind.
    """
    board = Board()

    all_tiles = [
        tile
        for row in board.tiles
        for tile in row
    ]

    all_tiles.append(board.spare_tile)

    portal_tiles = [
        tile
        for tile in all_tiles
        if tile.portal
    ]

    assert len(portal_tiles) == 2

    for tile in portal_tiles:
        assert tile.tile_type == TileType.CORNER