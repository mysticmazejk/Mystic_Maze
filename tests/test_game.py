import pytest

from app.game.enums import Direction, GateType, TileType
from app.game.game import Game
from app.game.target import Target
from app.game.tile import Tile


def create_started_game(
    targets_per_player: int = 1
) -> Game:
    """
    Erstellt ein gestartetes Spiel mit zwei Spielern.

    :param targets_per_player: Anzahl der Zielkarten pro Spieler.
    :return: Gestartetes Game-Objekt.
    """
    game = Game()

    game.add_player("Spieler 1")
    game.add_player("Spieler 2")

    game.start_game(
        targets_per_player
    )

    return game


def test_add_player():
    """
    Prüft, ob ein Spieler korrekt zum Spiel hinzugefügt wird.
    """
    game = Game()

    game.add_player("Spieler 1")

    assert len(game.players) == 1
    assert game.players[0].name == "Spieler 1"
    assert game.players[0].row == 0
    assert game.players[0].column == 0


def test_maximum_four_players():
    """
    Prüft, ob maximal vier Spieler hinzugefügt werden können.
    """
    game = Game()

    game.add_player("Spieler 1")
    game.add_player("Spieler 2")
    game.add_player("Spieler 3")
    game.add_player("Spieler 4")

    with pytest.raises(ValueError):
        game.add_player("Spieler 5")


def test_player_moves_with_shift():
    """
    Prüft, ob ein Spieler gemeinsam mit einer verschobenen Reihe
    bewegt wird.
    """
    game = create_started_game()

    player = game.players[0]

    # Spieler für den Test auf eine bewegliche Reihe setzen.
    player.row = 1
    player.column = 3

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    assert player.row == 1
    assert player.column == 4


def test_player_wraps_around_board():
    """
    Prüft, ob ein Spieler beim Herausschieben auf der gegenüberliegenden
    Seite wieder eingesetzt wird.
    """
    game = create_started_game()

    player = game.players[0]

    player.row = 1
    player.column = 6

    # Verhindert, dass ein zufällig als spare_tile gewähltes Portal
    # den Spieler nach dem Wrap direkt weiter teleportiert.
    game.board.spare_tile.portal = False

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    assert player.row == 1
    assert player.column == 0


def test_only_one_shift_per_turn():
    """
    Prüft, ob pro Zug nur einmal geschoben werden darf.
    """
    game = create_started_game()

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    with pytest.raises(
        ValueError,
        match="bereits verschoben"
    ):
        game.insert_spare_tile(
            3,
            Direction.SOUTH
        )


def test_cannot_move_before_shift():
    """
    Prüft, ob ein Spieler erst nach dem Verschieben des Labyrinths
    bewegt werden darf.
    """
    game = create_started_game()

    player = game.get_current_player()

    with pytest.raises(
        ValueError,
        match="zuerst das Labyrinth verschoben"
    ):
        game.move_player(
            player,
            player.row,
            player.column
        )


def test_end_turn_changes_player():
    """
    Prüft, ob nach dem Zug der nächste Spieler aktiv wird.
    """
    game = create_started_game()

    assert game.get_current_player().name == "Spieler 1"

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    game.end_turn()

    assert game.get_current_player().name == "Spieler 2"


def test_cannot_reverse_previous_shift():
    """
    Prüft, ob der vorherige Schiebezug nicht direkt rückgängig
    gemacht werden darf.
    """
    game = create_started_game()

    game.insert_spare_tile(
        3,
        Direction.EAST
    )

    game.end_turn()

    with pytest.raises(
        ValueError,
        match="nicht direkt rückgängig"
    ):
        game.insert_spare_tile(
            3,
            Direction.WEST
        )


def test_leaf_key_opens_only_leaf_gate():
    """
    Prüft, ob der Blattschlüssel nur das Blatttor öffnet.
    """
    game = Game()

    game.activate_key(
        Target.BLATTSCHLUESSEL
    )

    assert game.is_gate_open(GateType.LEAF)
    assert not game.is_gate_open(GateType.MOON)


def test_moon_key_opens_only_moon_gate():
    """
    Prüft, ob der Mondschlüssel nur das Mondtor öffnet.
    """
    game = Game()

    game.activate_key(
        Target.MONDSCHLUESSEL
    )

    assert game.is_gate_open(GateType.MOON)
    assert not game.is_gate_open(GateType.LEAF)


def test_normal_target_cannot_be_activated_as_key():
    """
    Prüft, ob ein normales Target nicht als Schlüssel aktiviert
    werden kann.
    """
    game = Game()

    with pytest.raises(ValueError):
        game.activate_key(
            Target.EULE
        )


def test_locked_gate_is_blocked():
    """
    Prüft, ob ein noch geschlossenes Tor bei der Wegfindung
    als gesperrtes Feld behandelt wird.
    """
    game = Game()

    # Kontrollierte Testumgebung erzeugen:
    # Alle Kacheln sind zunächst nur vertikal geöffnet.
    for row in range(game.board.SIZE):
        for column in range(game.board.SIZE):
            game.board.tiles[row][column] = Tile(
                TileType.STRAIGHT,
                rotation=0
            )

    # Horizontaler Weg:
    #
    # Spieler --> Blatttor --> Ziel
    #
    game.board.tiles[1][1] = Tile(
        TileType.STRAIGHT,
        rotation=1
    )

    game.board.tiles[1][2] = Tile(
        TileType.CROSS,
        gate=GateType.LEAF
    )

    game.board.tiles[1][3] = Tile(
        TileType.STRAIGHT,
        rotation=1
    )

    locked_positions = (
        game._get_locked_gate_positions()
    )

    reachable = (
        game.board.get_reachable_positions(
            1,
            1,
            blocked_positions=locked_positions
        )
    )

    # Das geschlossene Tor darf nicht betreten werden.
    assert (1, 2) not in reachable

    # Dadurch ist auch das Feld dahinter nicht erreichbar.
    assert (1, 3) not in reachable


def test_open_gate_is_reachable():
    """
    Prüft, ob ein Tor nach Aktivierung des passenden Schlüssels
    begehbar wird.
    """
    game = Game()

    # Kontrolliertes Testbrett erzeugen.
    for row in range(game.board.SIZE):
        for column in range(game.board.SIZE):
            game.board.tiles[row][column] = Tile(
                TileType.STRAIGHT,
                rotation=0
            )

    game.board.tiles[1][1] = Tile(
        TileType.STRAIGHT,
        rotation=1
    )

    game.board.tiles[1][2] = Tile(
        TileType.CROSS,
        gate=GateType.LEAF
    )

    game.board.tiles[1][3] = Tile(
        TileType.STRAIGHT,
        rotation=1
    )

    # Passenden Schlüssel aktivieren.
    game.activate_key(
        Target.BLATTSCHLUESSEL
    )

    locked_positions = (
        game._get_locked_gate_positions()
    )

    reachable = (
        game.board.get_reachable_positions(
            1,
            1,
            blocked_positions=locked_positions
        )
    )

    assert (1, 2) in reachable
    assert (1, 3) in reachable


def test_current_target_is_completed():
    """
    Prüft, ob das aktuelle persönliche Target beim Betreten
    der entsprechenden Kachel abgeschlossen wird.
    """
    game = Game()

    game.add_player("Spieler 1")

    player = game.get_current_player()

    player.targets = [
        Target.EULE,
        Target.DRACHE,
    ]

    # Spieler für den Test direkt auf die Eule setzen.
    player.row = 2
    player.column = 2

    game.board.tiles[2][2] = Tile(
        TileType.CORNER,
        target=Target.EULE
    )

    game._handle_target(
        player
    )

    assert player.completed_targets == [
        Target.EULE
    ]

    assert player.targets == [
        Target.DRACHE
    ]

    assert (
        player.get_current_target()
        == Target.DRACHE
    )


def test_wrong_target_is_not_completed():
    """
    Prüft, ob ein Target nicht abgeschlossen wird,
    wenn es nicht dem aktuell gesuchten Target entspricht.
    """
    game = Game()

    game.add_player("Spieler 1")

    player = game.get_current_player()

    player.targets = [
        Target.EULE,
        Target.DRACHE,
    ]

    player.row = 2
    player.column = 2

    # Spieler steht auf dem Drachen,
    # sucht aktuell aber die Eule.
    game.board.tiles[2][2] = Tile(
        TileType.CORNER,
        target=Target.DRACHE
    )

    game._handle_target(
        player
    )

    assert player.completed_targets == []

    assert player.targets == [
        Target.EULE,
        Target.DRACHE,
    ]

    assert (
        player.get_current_target()
        == Target.EULE
    )


def test_leaf_key_is_activated_when_found():
    """
    Prüft, ob der Blattschlüssel beim Betreten seiner
    Kachel global aktiviert wird.
    """
    game = Game()

    game.add_player("Spieler 1")

    player = game.get_current_player()

    player.row = 2
    player.column = 2

    game.board.tiles[2][2] = Tile(
        TileType.CORNER,
        target=Target.BLATTSCHLUESSEL
    )

    game._handle_target(
        player
    )

    assert (
        Target.BLATTSCHLUESSEL
        in game.activated_keys
    )

    assert game.is_gate_open(
        GateType.LEAF
    )

    assert not game.is_gate_open(
        GateType.MOON
    )


def test_portal_teleports_player_to_other_portal():
    """
    Prüft, ob ein Spieler von einem Portal zum zweiten
    Portal teleportiert wird.
    """
    game = Game()

    game.add_player("Spieler 1")

    player = game.get_current_player()

    # Vorhandene Portale entfernen,
    # damit der Test vollständig kontrolliert ist.
    for row in range(game.board.SIZE):
        for column in range(game.board.SIZE):
            game.board.tiles[row][column].portal = False

    # Zwei definierte Portalpositionen setzen.
    game.board.tiles[1][1] = Tile(
        TileType.CORNER,
        portal=True
    )

    game.board.tiles[5][5] = Tile(
        TileType.CORNER,
        portal=True
    )

    player.row = 1
    player.column = 1

    game._use_portal(
        player
    )

    assert player.row == 5
    assert player.column == 5


def test_portal_does_not_work_if_other_portal_is_spare_tile():
    """
    Prüft, ob keine Teleportation stattfindet,
    wenn sich das zweite Portal aktuell außerhalb
    des Spielbretts als Schiebeplättchen befindet.
    """
    game = Game()

    game.add_player("Spieler 1")

    player = game.get_current_player()

    # Alle Portalmarkierungen auf dem Brett entfernen.
    for row in range(game.board.SIZE):
        for column in range(game.board.SIZE):
            game.board.tiles[row][column].portal = False

    # Nur ein Portal befindet sich auf dem Brett.
    game.board.tiles[1][1] = Tile(
        TileType.CORNER,
        portal=True
    )

    # Zweites Portal ist aktuell das Schiebeplättchen.
    game.board.spare_tile = Tile(
        TileType.CORNER,
        portal=True
    )

    player.row = 1
    player.column = 1

    game._use_portal(
        player
    )

    # Spieler bleibt auf seinem Portal stehen.
    assert player.row == 1
    assert player.column == 1


def test_keys_are_never_distributed_as_player_targets():
    """
    Prüft, ob Blattschlüssel und Mondschlüssel niemals
    als persönliche Zielkarten verteilt werden.
    """
    game = Game()

    game.add_player("Spieler 1")
    game.add_player("Spieler 2")

    game.distribute_targets(
        targets_per_player=11
    )

    for player in game.players:
        assert (
            Target.BLATTSCHLUESSEL
            not in player.targets
        )

        assert (
            Target.MONDSCHLUESSEL
            not in player.targets
        )


def test_normal_shift_does_not_trigger_new_tile_effect():
    """
    Prüft, ob ein normal mitverschobener Spieler keinen neuen
    Kacheleffekt auslöst, weil er auf derselben Kachel bleibt.
    """
    game = create_started_game()

    player = game.players[0]

    # Spieler auf eine verschiebbare Reihe setzen.
    player.row = 1
    player.column = 2

    player.targets = [
        Target.EULE
    ]

    # Die Kachel des Spielers selbst besitzt die Eule.
    game.board.tiles[1][2].target = Target.EULE

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    # Spieler wurde gemeinsam mit seiner Kachel verschoben.
    assert player.row == 1
    assert player.column == 3

    # Das Target darf dadurch nicht als neu gefunden gelten.
    assert player.targets == [
        Target.EULE
    ]

    assert player.completed_targets == []


def test_pushed_out_player_triggers_inserted_tile_effect():
    """
    Prüft, ob ein herausgeschobener Spieler auf der gegenüberliegenden
    Seite den Effekt der neu eingeschobenen Kachel auslöst.
    """
    game = create_started_game()

    player = game.players[0]

    # Spieler steht am rechten Rand der Reihe 1.
    player.row = 1
    player.column = 6

    player.targets = [
        Target.EULE
    ]

    # Das einzuschiebende freie Plättchen trägt die Eule.
    game.board.spare_tile.target = Target.EULE

    # Für diesen Test darf die Kachel kein Portal sein,
    # da der Spieler sonst anschließend teleportiert würde.
    game.board.spare_tile.portal = False

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    # Spieler erscheint links auf der eingeschobenen Kachel.
    assert player.row == 1
    assert player.column == 0

    # Die Eule wurde dadurch gefunden.
    assert player.targets == []

    assert player.completed_targets == [
        Target.EULE
    ]


def test_cannot_shift_before_game_start():
    """
    Prüft, ob vor dem Spielstart nicht geschoben werden darf.
    """
    game = Game()

    game.add_player("Spieler 1")
    game.add_player("Spieler 2")

    with pytest.raises(
        ValueError,
        match="noch nicht gestartet"
    ):
        game.insert_spare_tile(
            1,
            Direction.EAST
        )


def test_cannot_move_before_game_start():
    """
    Prüft, ob vor dem Spielstart keine Spielerbewegung
    durchgeführt werden darf.
    """
    game = Game()

    game.add_player("Spieler 1")
    game.add_player("Spieler 2")

    player = game.get_current_player()

    with pytest.raises(
        ValueError,
        match="noch nicht gestartet"
    ):
        game.move_player(
            player,
            player.row,
            player.column
        )


def test_cannot_end_turn_before_game_start():
    """
    Prüft, ob vor dem Spielstart kein Zug beendet werden kann.
    """
    game = Game()

    game.add_player("Spieler 1")
    game.add_player("Spieler 2")

    with pytest.raises(
        ValueError,
        match="noch nicht gestartet"
    ):
        game.end_turn()


def test_cannot_shift_after_game_finished():
    """
    Prüft, ob nach dem Spielende nicht mehr geschoben werden darf.
    """
    game = create_started_game()

    game.finished = True

    with pytest.raises(
        ValueError,
        match="bereits beendet"
    ):
        game.insert_spare_tile(
            1,
            Direction.EAST
        )


def test_cannot_move_after_game_finished():
    """
    Prüft, ob nach dem Spielende keine Spielerbewegung
    mehr durchgeführt werden darf.
    """
    game = create_started_game()

    player = game.get_current_player()

    game.finished = True

    with pytest.raises(
        ValueError,
        match="bereits beendet"
    ):
        game.move_player(
            player,
            player.row,
            player.column
        )


def test_cannot_end_turn_after_game_finished():
    """
    Prüft, ob nach dem Spielende kein weiterer Zug
    beendet werden darf.
    """
    game = create_started_game()

    game.finished = True

    with pytest.raises(
        ValueError,
        match="bereits beendet"
    ):
        game.end_turn()

def test_spare_tile_can_be_rotated_before_shift():
    game = create_started_game()

    old_rotation = game.board.spare_tile.rotation

    game.rotate_spare_tile()

    assert game.board.spare_tile.rotation == (
        old_rotation + 1
    ) % 4


def test_spare_tile_cannot_be_rotated_after_shift():
    game = create_started_game()

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    with pytest.raises(
        ValueError,
        match="nach dem Einschieben"
    ):
        game.rotate_spare_tile()

def test_player_does_not_win_with_open_targets():
    game = create_started_game()

    player = game.players[0]

    player.targets = [
        Target.EULE
    ]

    player.row = player.start_row
    player.column = player.start_column

    assert not game._check_winner(player)
    assert not game.finished
    assert game.winner is None


def test_player_does_not_win_away_from_start():
    game = create_started_game()

    player = game.players[0]

    player.targets.clear()

    player.row = 1
    player.column = 1

    assert not game._check_winner(player)
    assert not game.finished


def test_player_wins_after_all_targets_and_return_to_start():
    game = create_started_game()

    player = game.players[0]

    player.targets.clear()

    player.row = player.start_row
    player.column = player.start_column

    assert game._check_winner(player)

    assert game.finished
    assert game.winner == player


def test_game_requires_two_players_to_start():
    game = Game()

    game.add_player("Spieler 1")

    with pytest.raises(
        ValueError,
        match="mindestens zwei Spieler"
    ):
        game.start_game(1)


def test_game_cannot_be_started_twice():
    game = create_started_game()

    with pytest.raises(
        ValueError,
        match="bereits gestartet"
    ):
        game.start_game(1)


def test_players_cannot_be_added_after_start():
    game = create_started_game()

    with pytest.raises(
        ValueError,
        match="Nach Spielstart"
    ):
        game.add_player("Spieler 3")