import pytest

from app.game_manager import GameManager
from app.game.enums import Direction


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

    assert len(game_id) == manager.GAME_ID_LENGTH


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
    Prüft, ob ein Spiel entfernt werden kann.
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
    abgerufen werden kann.
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
    Prüft, ob ein Spieler einem Spiel hinzugefügt werden kann.
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
    Prüft, ob ein leerer Spielername abgelehnt wird.
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
    Prüft, ob ein Spiel über den GameManager gestartet werden kann.
    """
    manager = GameManager()

    game_id = manager.create_game()

    manager.add_player(
        game_id,
        "Spieler 1"
    )

    manager.add_player(
        game_id,
        "Spieler 2"
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


def test_cannot_add_player_after_game_start():
    """
    Prüft, ob die Game-Regel für den Beitritt nach Spielstart
    auch über den GameManager gilt.
    """
    manager = GameManager()

    game_id = manager.create_game()

    manager.add_player(
        game_id,
        "Spieler 1"
    )

    manager.add_player(
        game_id,
        "Spieler 2"
    )

    manager.start_game(
        game_id,
        targets_per_player=1
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

    game_id = manager.create_game()

    manager.add_player(
        game_id,
        "Spieler 1"
    )

    manager.add_player(
        game_id,
        "Spieler 2"
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

    game_id = manager.create_game()

    manager.add_player(
        game_id,
        "Spieler 1"
    )

    manager.add_player(
        game_id,
        "Spieler 2"
    )

    manager.start_game(
        game_id,
        3
    )

    state = manager.get_public_game_state(
        game_id
    )

    assert len(
        state.board.tiles
    ) == 7

    for row in state.board.tiles:
        assert len(row) == 7

    assert state.board.spare_tile is not None


def test_public_state_contains_reachable_positions():
    """
    Prüft, ob der öffentliche Spielzustand nach dem
    Verschieben die erreichbaren Felder enthält.
    """
    manager = GameManager()

    game_id = manager.create_game()

    manager.add_player(
        game_id,
        "Spieler 1"
    )

    manager.add_player(
        game_id,
        "Spieler 2"
    )

    manager.start_game(
        game_id,
        1
    )

    game = manager.get_game(
        game_id
    )

    game.insert_spare_tile(
        1,
        Direction.EAST
    )

    state = manager.get_public_game_state(
        game_id
    )

    assert len(
        state.reachable_positions
    ) > 0