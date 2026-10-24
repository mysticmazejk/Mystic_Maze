import pytest

from app.game.enums import (
    CharacterType,
    Direction,
)
from app.game_manager import GameManager


def create_game_with_two_players(
    manager: GameManager
) -> str:
    """
    Erstellt über einen GameManager ein Spiel mit zwei Spielern.

    Das Spiel wird dabei noch nicht gestartet und es werden
    noch keine Charaktere vergeben.

    :param manager: Zu verwendender GameManager.
    :return: ID des erzeugten Spiels.
    """
    game_id = manager.create_game()

    manager.add_player(
        game_id,
        "Spieler 1"
    )

    manager.add_player(
        game_id,
        "Spieler 2"
    )

    return game_id


def select_standard_characters(
    manager: GameManager,
    game_id: str
) -> None:
    """
    Vergibt die beiden aktuell verfügbaren Charaktere
    an die beiden Spieler eines Testspiels.

    Spieler 0 erhält den Magier.
    Spieler 1 erhält den Wächter.

    Die Charakterauswahl erfolgt momentan direkt am Game-Objekt,
    da der GameManager hierfür noch keine eigene öffentliche
    Methode bereitstellt.

    :param manager: GameManager des Testspiels.
    :param game_id: ID des Spiels.
    """
    game = manager.get_game(
        game_id
    )

    game.select_character(
        0,
        CharacterType.MAGICIAN
    )

    game.select_character(
        1,
        CharacterType.GUARDIAN
    )


def create_started_game(
    manager: GameManager,
    targets_per_player: int = 1
) -> str:
    """
    Erstellt und startet ein vollständiges Testspiel.

    Vor dem Start werden die beiden verfügbaren Charaktere
    eindeutig an die Spieler vergeben.

    :param manager: Zu verwendender GameManager.
    :param targets_per_player: Anzahl persönlicher Ziele pro Spieler.
    :return: ID des gestarteten Spiels.
    """
    game_id = create_game_with_two_players(
        manager
    )

    select_standard_characters(
        manager,
        game_id
    )

    manager.start_game(
        game_id,
        targets_per_player
    )

    return game_id


def test_create_game():
    """
    Prüft, ob ein neues Spiel erstellt und gespeichert wird.
    """
    manager = GameManager()

    game_id = manager.create_game()

    assert game_id in manager.games
    assert manager.get_game(game_id) is not None


def test_game_id_has_correct_length():
    """
    Prüft, ob die erzeugte Spiel-ID die vorgesehene Länge besitzt.
    """
    manager = GameManager()

    game_id = manager.create_game()

    assert (
        len(game_id)
        == manager.GAME_ID_LENGTH
    )


def test_created_games_have_different_ids():
    """
    Prüft, ob unterschiedliche Spiele unterschiedliche IDs erhalten.
    """
    manager = GameManager()

    first_game_id = manager.create_game()
    second_game_id = manager.create_game()

    assert first_game_id != second_game_id


def test_get_unknown_game_fails():
    """
    Prüft, ob der Zugriff auf ein unbekanntes Spiel fehlschlägt.
    """
    manager = GameManager()

    with pytest.raises(
        ValueError,
        match="nicht gefunden"
    ):
        manager.get_game(
            "ABC123"
        )


def test_remove_game():
    """
    Prüft, ob ein vorhandenes Spiel entfernt werden kann.
    """
    manager = GameManager()

    game_id = manager.create_game()

    manager.remove_game(
        game_id
    )

    assert game_id not in manager.games


def test_removed_game_cannot_be_accessed():
    """
    Prüft, ob ein entferntes Spiel anschließend nicht mehr
    über den GameManager abgerufen werden kann.
    """
    manager = GameManager()

    game_id = manager.create_game()

    manager.remove_game(
        game_id
    )

    with pytest.raises(
        ValueError,
        match="nicht gefunden"
    ):
        manager.get_game(
            game_id
        )


def test_add_player_to_game():
    """
    Prüft, ob ein Spieler einem Spiel hinzugefügt werden kann
    und der korrekte Spielerindex zurückgegeben wird.
    """
    manager = GameManager()

    game_id = manager.create_game()

    player_index = manager.add_player(
        game_id,
        "Spieler 1"
    )

    game = manager.get_game(
        game_id
    )

    player = manager.get_player(
        game_id,
        player_index
    )

    assert len(game.players) == 1
    assert player_index == 0
    assert player.name == "Spieler 1"


def test_player_name_is_trimmed():
    """
    Prüft, ob Leerzeichen am Anfang und Ende eines
    Spielernamens entfernt werden.
    """
    manager = GameManager()

    game_id = manager.create_game()

    player_index = manager.add_player(
        game_id,
        "  Spieler 1  "
    )

    player = manager.get_player(
        game_id,
        player_index
    )

    assert player.name == "Spieler 1"


def test_empty_player_name_is_rejected():
    """
    Prüft, ob ein leerer oder nur aus Leerzeichen
    bestehender Spielername abgelehnt wird.
    """
    manager = GameManager()

    game_id = manager.create_game()

    with pytest.raises(
        ValueError,
        match="nicht leer"
    ):
        manager.add_player(
            game_id,
            "   "
        )


def test_duplicate_player_name_is_rejected():
    """
    Prüft, ob ein Spielername innerhalb eines Spiels
    nur einmal vergeben werden kann.
    """
    manager = GameManager()

    game_id = manager.create_game()

    manager.add_player(
        game_id,
        "Spieler 1"
    )

    with pytest.raises(
        ValueError,
        match="bereits vergeben"
    ):
        manager.add_player(
            game_id,
            "Spieler 1"
        )


def test_duplicate_player_name_is_case_insensitive():
    """
    Prüft, ob Spielernamen unabhängig von Groß- und
    Kleinschreibung eindeutig sein müssen.
    """
    manager = GameManager()

    game_id = manager.create_game()

    manager.add_player(
        game_id,
        "Noah"
    )

    with pytest.raises(
        ValueError,
        match="bereits vergeben"
    ):
        manager.add_player(
            game_id,
            "NOAH"
        )


def test_start_game():
    """
    Prüft, ob ein vollständig vorbereitetes Spiel
    über den GameManager gestartet werden kann.

    Vor dem Start müssen beide Spieler einen eindeutigen
    Charakter gewählt haben.
    """
    manager = GameManager()

    game_id = create_game_with_two_players(
        manager
    )

    select_standard_characters(
        manager,
        game_id
    )

    manager.start_game(
        game_id,
        targets_per_player=3
    )

    game = manager.get_game(
        game_id
    )

    assert game.started
    assert not game.finished

    assert len(
        game.players[0].targets
    ) == 3

    assert len(
        game.players[1].targets
    ) == 3


def test_game_manager_cannot_start_without_character_selection():
    """
    Prüft, ob die Charakterpflicht der Game-Klasse
    auch bei einem Start über den GameManager greift.
    """
    manager = GameManager()

    game_id = create_game_with_two_players(
        manager
    )

    with pytest.raises(
        ValueError,
        match="Charakter wählen"
    ):
        manager.start_game(
            game_id,
            targets_per_player=1
        )


def test_cannot_add_player_after_game_start():
    """
    Prüft, ob die Game-Regel für den Beitritt nach Spielstart
    auch über den GameManager gilt.
    """
    manager = GameManager()

    game_id = create_started_game(
        manager
    )

    with pytest.raises(
        ValueError,
        match="Nach Spielstart"
    ):
        manager.add_player(
            game_id,
            "Spieler 3"
        )


def test_add_player_returns_player_index():
    """
    Prüft, ob beim Beitritt der feste Spielerindex zurückgegeben wird.
    """
    manager = GameManager()

    game_id = manager.create_game()

    first_index = manager.add_player(
        game_id,
        "Spieler 1"
    )

    second_index = manager.add_player(
        game_id,
        "Spieler 2"
    )

    assert first_index == 0
    assert second_index == 1


def test_game_manager_get_player_by_index():
    """
    Prüft, ob der GameManager einen Spieler anhand
    seines Index zurückgeben kann.
    """
    manager = GameManager()

    game_id = create_game_with_two_players(
        manager
    )

    player = manager.get_player(
        game_id,
        1
    )

    assert player.name == "Spieler 2"


def test_public_game_state_contains_complete_board():
    """
    Prüft, ob der öffentliche Spielzustand
    das vollständige 7x7-Spielbrett enthält.
    """
    manager = GameManager()

    game_id = create_started_game(
        manager,
        targets_per_player=3
    )

    state = manager.get_public_game_state(
        game_id
    )

    assert len(
        state.board.tiles
    ) == 7

    # Jede der sieben Zeilen muss wiederum
    # genau sieben Kacheln enthalten.
    for row in state.board.tiles:
        assert len(row) == 7

    assert state.board.spare_tile is not None


def test_public_state_contains_reachable_positions():
    """
    Prüft, ob der öffentliche Spielzustand nach dem
    Verschieben die erreichbaren Felder des aktiven
    Spielers enthält.
    """
    manager = GameManager()

    game_id = create_started_game(
        manager
    )

    game = manager.get_game(
        game_id
    )

    # Erst nach dem verpflichtenden Verschieben
    # werden Bewegungsziele angeboten.
    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    state = manager.get_public_game_state(
        game_id
    )

    # Mindestens die eigene Spielerposition
    # muss erreichbar sein.
    assert len(
        state.reachable_positions
    ) > 0