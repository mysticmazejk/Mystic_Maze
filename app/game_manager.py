import secrets

from app.game.enums import Direction
from app.game.game import Game
from app.game.player import Player
from app.game.tile import Tile
from app.schemas.game_schemas import (
    BoardPublicState,
    GamePublicState,
    PlayerPrivateState,
    PlayerPublicState,
    PositionPublicState,
    ShiftOptionPublicState,
    TilePublicState,
)


class GameManager:
    """
    Verwaltet alle aktuell vorhandenen Spiele.
    """

    GAME_ID_LENGTH = 6

    GAME_ID_CHARACTERS = (
        "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    )

    def __init__(self):
        self.games: dict[str, Game] = {}

    def create_game(self) -> str:
        """
        Erstellt ein neues Spiel.

        :return: Eindeutige ID des neuen Spiels.
        """
        game_id = self._generate_game_id()

        self.games[game_id] = Game()

        return game_id

    def get_game(self, game_id: str) -> Game:
        """
        Gibt ein vorhandenes Spiel zurück.

        :param game_id: ID des Spiels.
        :return: Gefundene Game-Instanz.
        :raises ValueError: Wenn das Spiel nicht existiert.
        """
        game = self.games.get(
            game_id.upper()
        )

        if game is None:
            raise ValueError(
                f"Spiel '{game_id}' wurde nicht gefunden."
            )

        return game

    def remove_game(self, game_id: str) -> None:
        """
        Entfernt ein vorhandenes Spiel.

        :param game_id: ID des Spiels.
        :raises ValueError: Wenn das Spiel nicht existiert.
        """
        game_id = game_id.upper()

        if game_id not in self.games:
            raise ValueError(
                f"Spiel '{game_id}' wurde nicht gefunden."
            )

        del self.games[game_id]

    def add_player(
        self,
        game_id: str,
        name: str
    ) -> int:
        """
        Fügt einem Spiel einen Spieler hinzu.

        Der Index des Spielers in der Spielerliste dient
        gleichzeitig als technische Spieler-ID.

        :param game_id: ID des Spiels.
        :param name: Anzeigename des Spielers.
        :return: Index des neuen Spielers.
        """
        game = self.get_game(
            game_id
        )

        name = name.strip()

        if not name:
            raise ValueError(
                "Der Spielername darf nicht leer sein."
            )

        if any(
            player.name.casefold() == name.casefold()
            for player in game.players
        ):
            raise ValueError(
                f"Der Spielername '{name}' ist bereits vergeben."
            )

        game.add_player(
            name
        )

        return len(game.players) - 1

    def get_player(
        self,
        game_id: str,
        player_index: int
    ) -> Player:
        """
        Gibt einen Spieler anhand seines Index zurück.

        :param game_id: ID des Spiels.
        :param player_index: Index des Spielers.
        :return: Gefundener Spieler.
        """
        game = self.get_game(
            game_id
        )

        return game.get_player(
            player_index
        )

    def start_game(
        self,
        game_id: str,
        targets_per_player: int
    ) -> None:
        """
        Startet ein vorhandenes Spiel.

        :param game_id: ID des Spiels.
        :param targets_per_player: Anzahl der Zielkarten pro Spieler.
        """
        game = self.get_game(
            game_id
        )

        game.start_game(
            targets_per_player
        )

    def _generate_game_id(self) -> str:
        """
        Erzeugt eine eindeutige Spiel-ID.

        :return: Neu erzeugte Spiel-ID.
        """
        while True:
            game_id = "".join(
                secrets.choice(
                    self.GAME_ID_CHARACTERS
                )
                for _ in range(
                    self.GAME_ID_LENGTH
                )
            )

            if game_id not in self.games:
                return game_id

    def get_public_game_state(
            self,
            game_id: str
    ) -> GamePublicState:
        """
        Erstellt den öffentlich sichtbaren Zustand eines Spiels.

        Persönliche Zielkarten der Spieler werden dabei
        nicht veröffentlicht.

        :param game_id: ID des Spiels.
        :return: Öffentlicher Spielzustand.
        """

        game = self.get_game(
            game_id
        )

        players = [
            PlayerPublicState(
                player_index=index,
                name=player.name,
                row=player.row,
                column=player.column,
                completed_target_count=len(
                    player.completed_targets
                )
            )
            for index, player in enumerate(
                game.players
            )
        ]

        winner_index = None

        if game.winner is not None:
            winner_index = game.players.index(
                game.winner
            )

        board = (
            self._create_board_public_state(
                game
            )
        )

        reachable_positions = [
            PositionPublicState(
                row=row,
                column=column
            )
            for row, column
            in sorted(
                game.get_reachable_positions_for_current_player()
            )
        ]

        return GamePublicState(
            game_id=game_id.upper(),
            started=game.started,
            finished=game.finished,
            current_player_index=(
                game.current_player_id
            ),
            has_shifted=game.has_shifted,
            has_moved=game.has_moved,
            winner_index=winner_index,
            board=board,
            players=players,
            reachable_positions=reachable_positions
        )

    def get_private_player_state(
            self,
            game_id: str,
            player_index: int
    ) -> PlayerPrivateState:
        """
        Erstellt den privaten Zustand eines einzelnen Spielers.

        :param game_id: ID des Spiels.
        :param player_index: Index des Spielers.
        :return: Privater Spielerzustand.
        """
        player = self.get_player(
            game_id,
            player_index
        )

        current_target = (
            player.get_current_target()
        )

        return PlayerPrivateState(
            player_index=player_index,
            current_target=(
                current_target.value
                if current_target is not None
                else None
            ),
            remaining_target_count=len(
                player.targets
            ),
            completed_targets=[
                target.value
                for target in player.completed_targets
            ]
        )

    def _ensure_current_player(
            self,
            game_id: str,
            player_index: int
    ) -> None:
        """
        Prüft, ob der angegebene Spieler aktuell am Zug ist.

        :param game_id: ID des Spiels.
        :param player_index: Index des Spielers.
        :raises ValueError: Wenn der Spieler nicht am Zug ist.
        """

        game = self.get_game(
            game_id
        )

        player = game.get_player(
            player_index
        )

        if player != game.get_current_player():
            raise ValueError(
                "Dieser Spieler ist aktuell nicht am Zug."
            )

    def rotate_spare_tile(
            self,
            game_id: str,
            player_index: int
    ) -> None:
        """
        Dreht das freie Schiebeplättchen.

        :param game_id: ID des Spiels.
        :param player_index: Index des ausführenden Spielers.
        """

        self._ensure_current_player(
            game_id,
            player_index
        )

        game = self.get_game(
            game_id
        )

        game.rotate_spare_tile()

    def shift_board(
            self,
            game_id: str,
            player_index: int,
            index: int,
            direction: Direction
    ) -> None:
        """
        Schiebt das freie Plättchen in das Labyrinth ein.

        :param game_id: ID des Spiels.
        :param player_index: Index des ausführenden Spielers.
        :param index: Zu verschiebende Reihe oder Spalte.
        :param direction: Richtung der Verschiebung.
        """

        self._ensure_current_player(
            game_id,
            player_index
        )

        game = self.get_game(
            game_id
        )

        game.insert_spare_tile(
            index,
            direction
        )

    def move_player(
            self,
            game_id: str,
            player_index: int,
            row: int,
            column: int
    ) -> None:
        """
        Bewegt einen Spieler.

        :param game_id: ID des Spiels.
        :param player_index: Index des Spielers.
        :param row: Zielzeile.
        :param column: Zielspalte.
        """

        game = self.get_game(
            game_id
        )

        player = game.get_player(
            player_index
        )

        game.move_player(
            player,
            row,
            column
        )

    def end_turn(
            self,
            game_id: str,
            player_index: int
    ) -> None:
        """
        Beendet den Zug des aktuell aktiven Spielers.

        :param game_id: ID des Spiels.
        :param player_index: Index des ausführenden Spielers.
        """

        self._ensure_current_player(
            game_id,
            player_index
        )

        game = self.get_game(
            game_id
        )

        game.end_turn()


    def _create_tile_public_state(
            self,
            game: Game,
            tile: Tile
    ) -> TilePublicState:
        """
        Wandelt eine interne Tile-Instanz in den öffentlich
        sichtbaren Zustand einer Kachel um.

        :param game: Zugehöriges Spiel.
        :param tile: Zu serialisierende Kachel.
        :return: Öffentlicher Kachelzustand.
        """

        gate_open = None

        # Nur Tor-Kacheln besitzen einen Torstatus.
        if tile.gate is not None:
            gate_open = game.is_gate_open(
                tile.gate
            )

        return TilePublicState(
            tile_type=tile.tile_type.value,
            rotation=tile.rotation,
            fixed=tile.fixed,
            gate=(
                tile.gate.value
                if tile.gate is not None
                else None
            ),
            gate_open=gate_open,
            portal=tile.portal,
            target=(
                tile.target.value
                if tile.target is not None
                else None
            )
        )

    def _create_board_public_state(
            self,
            game: Game
    ) -> BoardPublicState:
        """
        Erstellt den öffentlich sichtbaren Zustand
        des vollständigen Spielbretts.

        :param game: Zu serialisierendes Spiel.
        :return: Öffentlicher Board-Zustand.
        """

        tiles = []

        for row in range(
                game.board.SIZE
        ):
            tile_row = []

            for column in range(
                    game.board.SIZE
            ):
                tile = game.board.get_tile(
                    row,
                    column
                )

                tile_row.append(
                    self._create_tile_public_state(
                        game,
                        tile
                    )
                )

            tiles.append(
                tile_row
            )

        spare_tile = (
            self._create_tile_public_state(
                game,
                game.board.spare_tile
            )
        )

        allowed_shifts = [
            ShiftOptionPublicState(
                index=index,
                direction=direction.value
            )
            for index, direction
            in game.get_allowed_shifts()
        ]

        return BoardPublicState(
            tiles=tiles,
            spare_tile=spare_tile,
            allowed_shifts=allowed_shifts
        )