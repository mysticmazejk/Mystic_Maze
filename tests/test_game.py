import pytest

from app.game.enums import (
    CharacterType,
    Direction,
    GateType,
    RotationDirection,
    TileType,
)
from app.game.game import Game
from app.game.player import Player
from app.game.target import Target
from app.game.tile import Tile


def create_started_game(
    targets_per_player: int = 1
) -> Game:
    """
    Erstellt ein gestartetes Standard-Testspiel mit zwei Spielern.

    Spieler 0 erhält den Charakter Magier und Spieler 1 den Charakter
    Wächter. Dadurch erfüllt das Testspiel die verpflichtende
    Charakterauswahl vor dem Spielstart.

    :param targets_per_player: Anzahl der Zielkarten pro Spieler.
    :return: Vollständig gestartetes Game-Objekt.
    """
    game = Game()

    game.add_player("Spieler 1")
    game.add_player("Spieler 2")

    # Ein gestartetes Spiel benötigt für jeden Spieler
    # einen eindeutig vergebenen Charakter.
    game.select_character(
        0,
        CharacterType.MAGICIAN
    )

    game.select_character(
        1,
        CharacterType.GUARDIAN
    )

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

    # Verhindert, dass ein zufällig als Spare Tile gewähltes Portal
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

    assert game.is_gate_open(
        GateType.LEAF
    )

    assert not game.is_gate_open(
        GateType.MOON
    )


def test_moon_key_opens_only_moon_gate():
    """
    Prüft, ob der Mondschlüssel nur das Mondtor öffnet.
    """
    game = Game()

    game.activate_key(
        Target.MONDSCHLUESSEL
    )

    assert game.is_gate_open(
        GateType.MOON
    )

    assert not game.is_gate_open(
        GateType.LEAF
    )


def test_normal_target_cannot_be_activated_as_key():
    """
    Prüft, ob ein normales Target nicht als Schlüssel
    aktiviert werden kann.
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

    # Kontrollierte Testumgebung:
    # Alle Kacheln werden zunächst nur vertikal geöffnet.
    for row in range(game.board.SIZE):
        for column in range(game.board.SIZE):
            game.board.tiles[row][column] = Tile(
                TileType.STRAIGHT,
                rotation=0
            )

    # Anschließend wird ein horizontaler Testweg erzeugt:
    #
    # Spieler -> Blatttor -> Ziel
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

    # Das geschlossene Tor selbst darf nicht betreten werden.
    assert (1, 2) not in reachable

    # Dadurch ist auch das Feld hinter dem Tor nicht erreichbar.
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

    # Der passende Schlüssel wird global aktiviert.
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

    # Vorhandene Portale entfernen, damit der Test
    # vollständig kontrolliert durchgeführt werden kann.
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

    # Nur ein Portal befindet sich auf dem Spielbrett.
    game.board.tiles[1][1] = Tile(
        TileType.CORNER,
        portal=True
    )

    # Das zweite Portal ist aktuell das freie Schiebeplättchen.
    game.board.spare_tile = Tile(
        TileType.CORNER,
        portal=True
    )

    player.row = 1
    player.column = 1

    game._use_portal(
        player
    )

    # Ohne zweites Portal auf dem Board findet
    # keine Teleportation statt.
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

    # Die Eule wurde durch das tatsächliche Betreten
    # der neu eingeschobenen Kachel gefunden.
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
    """
    Prüft, ob das freie Schiebeplättchen vor dem Einschieben
    im aktuellen Zug gedreht werden kann.
    """
    game = create_started_game()

    old_rotation = (
        game.board.spare_tile.rotation
    )

    game.rotate_spare_tile()

    assert (
        game.board.spare_tile.rotation
        == (old_rotation + 1) % 4
    )


def test_spare_tile_cannot_be_rotated_after_shift():
    """
    Prüft, ob das freie Schiebeplättchen nach dem Einschieben
    im selben Zug nicht mehr gedreht werden kann.
    """
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
    """
    Prüft, ob ein Spieler auf seinem Startfeld nicht gewinnt,
    solange noch persönliche Ziele offen sind.
    """
    game = create_started_game()

    player = game.players[0]

    player.targets = [
        Target.EULE
    ]

    player.row = player.start_row
    player.column = player.start_column

    assert not game._check_winner(
        player
    )

    assert not game.finished
    assert game.winner is None


def test_player_wins_after_all_targets():
    """
    Prüft, ob ein Spieler gewinnt, wenn alle persönlichen Ziele
    abgeschlossen sind
    """
    game = create_started_game()

    player = game.players[0]

    player.targets.clear()

    assert game._check_winner(
        player
    )

    assert game.finished
    assert game.winner == player


def test_game_requires_two_players_to_start():
    """
    Prüft, ob ein Spiel erst mit mindestens zwei Spielern
    gestartet werden kann.
    """
    game = Game()

    game.add_player("Spieler 1")

    with pytest.raises(
        ValueError,
        match="mindestens zwei Spieler"
    ):
        game.start_game(1)


def test_game_cannot_be_started_twice():
    """
    Prüft, ob ein bereits gestartetes Spiel nicht erneut
    gestartet werden kann.
    """
    game = create_started_game()

    with pytest.raises(
        ValueError,
        match="bereits gestartet"
    ):
        game.start_game(1)


def test_players_cannot_be_added_after_start():
    """
    Prüft, ob nach dem Spielstart keine weiteren Spieler
    mehr hinzugefügt werden können.
    """
    game = create_started_game()

    with pytest.raises(
        ValueError,
        match="Nach Spielstart"
    ):
        game.add_player(
            "Spieler 3"
        )


def test_get_player_by_index():
    """
    Prüft, ob ein Spieler anhand seines Index gefunden wird.
    """
    game = Game()

    game.add_player("Spieler 1")
    game.add_player("Spieler 2")

    player = game.get_player(
        1
    )

    assert player.name == "Spieler 2"


def test_get_player_with_invalid_index_fails():
    """
    Prüft, ob ein ungültiger Spielerindex abgelehnt wird.
    """
    game = Game()

    game.add_player("Spieler 1")

    with pytest.raises(
        ValueError,
        match="nicht gefunden"
    ):
        game.get_player(
            1
        )


def test_negative_player_index_fails():
    """
    Prüft, ob negative Spielerindizes nicht zugelassen werden.
    """
    game = Game()

    game.add_player("Spieler 1")

    with pytest.raises(
        ValueError,
        match="nicht gefunden"
    ):
        game.get_player(
            -1
        )


def test_all_shifts_available_at_start():
    """
    Prüft, ob zu Beginn eines Zuges alle zwölf
    Einschubmöglichkeiten verfügbar sind.
    """
    game = create_started_game()

    allowed_shifts = (
        game.get_allowed_shifts()
    )

    # Drei verschiebbare Reihen/Spalten mit jeweils
    # vier möglichen Einschubrichtungen ergeben 12 Optionen.
    assert len(allowed_shifts) == 12


def test_no_shift_available_after_shift():
    """
    Prüft, ob nach dem Einschieben keine weitere
    Schiebeaktion im selben Zug möglich ist.
    """
    game = create_started_game()

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    assert (
        game.get_allowed_shifts()
        == []
    )


def test_reverse_shift_not_available_next_turn():
    """
    Prüft, ob der vorherige Schiebezug im nächsten Zug
    nicht unmittelbar rückgängig gemacht werden kann.
    """
    game = create_started_game()

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    game.end_turn()

    allowed_shifts = (
        game.get_allowed_shifts()
    )

    # Der direkte Gegenzug auf demselben Index
    # muss aus den erlaubten Optionen entfernt sein.
    assert (
        1,
        Direction.WEST
    ) not in allowed_shifts

    assert len(allowed_shifts) == 11


def test_no_reachable_positions_before_shift():
    """
    Prüft, ob vor dem Verschieben noch keine
    Bewegungsziele angeboten werden.
    """
    game = create_started_game()

    assert (
        game.get_reachable_positions_for_current_player()
        == set()
    )


def test_reachable_positions_available_after_shift():
    """
    Prüft, ob nach dem Verschieben erreichbare
    Positionen ermittelt werden.
    """
    game = create_started_game()

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    reachable_positions = (
        game.get_reachable_positions_for_current_player()
    )

    player = game.get_current_player()

    # Die eigene Position gehört bei der Wegfindung ebenfalls
    # zur Menge der erreichbaren Positionen.
    assert (
        player.row,
        player.column
    ) in reachable_positions


def test_no_reachable_positions_after_player_moved():
    """
    Prüft, ob nach einer bereits erfolgten Bewegung
    keine weiteren Bewegungsziele angeboten werden.
    """
    game = create_started_game()

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    player = game.get_current_player()

    reachable_positions = (
        game.get_reachable_positions_for_current_player()
    )

    target_row, target_column = next(
        iter(reachable_positions)
    )

    game.move_player(
        player,
        target_row,
        target_column
    )

    assert (
        game.get_reachable_positions_for_current_player()
        == set()
    )


def test_character_cannot_be_selected_twice():
    """
    Prüft, ob derselbe Charakter innerhalb einer Partie
    nicht gleichzeitig von mehreren Spielern gewählt werden kann.
    """
    game = Game()

    game.add_player("Spieler 1")
    game.add_player("Spieler 2")

    game.select_character(
        0,
        CharacterType.MAGICIAN
    )

    # Der Magier ist bereits vergeben und darf deshalb
    # nicht zusätzlich Spieler 1 zugewiesen werden.
    with pytest.raises(
        ValueError,
        match="bereits vergeben"
    ):
        game.select_character(
            1,
            CharacterType.MAGICIAN
        )


def test_game_cannot_start_without_character_selection():
    """
    Prüft, ob das Spiel nicht gestartet werden kann,
    solange mindestens ein Spieler keinen Charakter gewählt hat.
    """
    game = Game()

    game.add_player("Spieler 1")
    game.add_player("Spieler 2")

    # Nur Spieler 0 wählt einen Charakter.
    # Spieler 1 besitzt weiterhin character=None.
    game.select_character(
        0,
        CharacterType.MAGICIAN
    )

    with pytest.raises(
        ValueError,
        match="Charakter wählen"
    ):
        game.start_game(
            1
        )


def test_guardian_can_pass_closed_gate():
    """
    Prüft die passive Fähigkeit des Wächters.

    Für den Wächter dürfen geschlossene Tore bei der Berechnung
    seiner Bewegungsmöglichkeiten nicht als blockierte Positionen
    behandelt werden.
    """
    game = Game()

    game.add_player("Wächter")
    game.add_player("Magier")

    game.select_character(
        0,
        CharacterType.GUARDIAN
    )

    player = game.players[0]

    blocked_positions = (
        game._get_blocked_positions_for_player(
            player
        )
    )

    # Der Wächter ignoriert geschlossene Tore vollständig.
    assert blocked_positions == set()


def test_magician_ability_rotates_tile_right():
    """
    Prüft, ob der Magier eine bewegliche Kachel
    um 90 Grad nach rechts drehen kann.
    """
    game = Game()

    game.add_player("Magier")
    game.add_player("Wächter")

    game.select_character(
        0,
        CharacterType.MAGICIAN
    )

    game.select_character(
        1,
        CharacterType.GUARDIAN
    )

    game.start_game(
        1
    )

    player = game.players[0]

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    old_rotation = (
        game.board.tiles[1][1].rotation
    )

    game.use_magician_ability(
        player,
        1,
        1,
        RotationDirection.RIGHT
    )

    assert (
        game.board.tiles[1][1].rotation
        == (old_rotation + 1) % 4
    )

    assert (
        player.ability_used_for_current_target
        is True
    )


def test_magician_ability_rotates_tile_left():
    """
    Prüft, ob der Magier eine bewegliche Kachel
    um 90 Grad nach links drehen kann.
    """
    game = Game()

    game.add_player("Magier")
    game.add_player("Wächter")

    game.select_character(
        0,
        CharacterType.MAGICIAN
    )

    game.select_character(
        1,
        CharacterType.GUARDIAN
    )

    game.start_game(
        1
    )

    player = game.players[0]

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    old_rotation = (
        game.board.tiles[1][1].rotation
    )

    game.use_magician_ability(
        player,
        1,
        1,
        RotationDirection.LEFT
    )

    assert (
        game.board.tiles[1][1].rotation
        == (old_rotation - 1) % 4
    )

    assert (
        player.ability_used_for_current_target
        is True
    )


def test_magician_left_rotation_wraps_from_zero_to_three():
    """
    Prüft den Wraparound bei einer Linksdrehung
    von Rotation 0 auf Rotation 3.
    """
    game = Game()

    game.add_player("Magier")
    game.add_player("Wächter")

    game.select_character(
        0,
        CharacterType.MAGICIAN
    )

    game.select_character(
        1,
        CharacterType.GUARDIAN
    )

    game.start_game(
        1
    )

    player = game.players[0]

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    game.board.tiles[1][1].rotation = 0

    game.use_magician_ability(
        player,
        1,
        1,
        RotationDirection.LEFT
    )

    assert (
        game.board.tiles[1][1].rotation
        == 3
    )


def test_magician_right_rotation_wraps_from_three_to_zero():
    """
    Prüft den Wraparound bei einer Rechtsdrehung
    von Rotation 3 auf Rotation 0.
    """
    game = Game()

    game.add_player("Magier")
    game.add_player("Wächter")

    game.select_character(
        0,
        CharacterType.MAGICIAN
    )

    game.select_character(
        1,
        CharacterType.GUARDIAN
    )

    game.start_game(
        1
    )

    player = game.players[0]

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    game.board.tiles[1][1].rotation = 3

    game.use_magician_ability(
        player,
        1,
        1,
        RotationDirection.RIGHT
    )

    assert (
        game.board.tiles[1][1].rotation
        == 0
    )


def test_magician_ability_can_only_be_used_once_per_target():
    """
    Prüft, ob die Magier-Fähigkeit unabhängig von der
    gewählten Drehrichtung nur einmal pro aktuellem Ziel
    verwendet werden kann.
    """
    game = Game()

    game.add_player("Magier")
    game.add_player("Wächter")

    game.select_character(
        0,
        CharacterType.MAGICIAN
    )

    game.select_character(
        1,
        CharacterType.GUARDIAN
    )

    game.start_game(
        1
    )

    player = game.players[0]

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    game.use_magician_ability(
        player,
        1,
        1,
        RotationDirection.RIGHT
    )

    assert (
        player.ability_used_for_current_target
        is True
    )

    with pytest.raises(
        ValueError,
        match="bereits verwendet"
    ):
        game.use_magician_ability(
            player,
            1,
            2,
            RotationDirection.LEFT
        )


def test_magician_ability_resets_after_target_completion():
    """
    Prüft, ob die Magier-Fähigkeit beim Wechsel zum nächsten
    persönlichen Ziel wieder verfügbar wird.
    """
    player = Player(
        name="Magier",
        row=0,
        column=0,
        character=CharacterType.MAGICIAN
    )

    player.targets = [
        Target.EULE,
        Target.DRACHE,
    ]

    # Für das aktuelle Ziel "Eule" wurde die Fähigkeit
    # bereits verwendet.
    player.ability_used_for_current_target = True

    player.complete_current_target()

    # Nach Abschluss der Eule wird der Drache
    # zum neuen aktuellen persönlichen Ziel.
    assert (
        player.get_current_target()
        == Target.DRACHE
    )

    # Da ein neues Ziel gesucht wird, darf der Magier
    # seine Fähigkeit erneut verwenden.
    assert (
        player.ability_used_for_current_target
        is False
    )

def test_magician_cannot_rotate_fixed_tile():
    """
    Prüft, ob der Magier keine feste Kachel
    des Spielbretts drehen kann.

    Ein abgelehnter Versuch darf die Fähigkeit
    für das aktuelle Ziel nicht verbrauchen.
    """
    game = Game()

    game.add_player("Magier")
    game.add_player("Wächter")

    game.select_character(
        0,
        CharacterType.MAGICIAN
    )

    game.select_character(
        1,
        CharacterType.GUARDIAN
    )

    game.start_game(1)

    player = game.players[0]

    # Die Magier-Fähigkeit ist erst nach
    # dem regulären Einschieben verfügbar.
    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    # Position (2, 2) gehört zu den festen
    # Kacheln des Spielbretts.
    tile = game.board.tiles[2][2]

    assert tile.fixed is True

    old_rotation = tile.rotation

    with pytest.raises(
        ValueError,
        match="Feste Kacheln"
    ):
        game.use_magician_ability(
            player,
            2,
            2,
            RotationDirection.RIGHT
        )

    # Die feste Kachel bleibt unverändert.
    assert tile.rotation == old_rotation

    # Ein ungültiger Versuch verbraucht
    # die Fähigkeit nicht.
    assert (
        player.ability_used_for_current_target
        is False
    )