import random

from app.game.board import Board
from app.game.enums import Direction, GateType
from app.game.player import Player
from app.game.target import Target



class Game:
    KEY_TO_GATE = {
        Target.BLATTSCHLUESSEL: GateType.LEAF,
        Target.MONDSCHLUESSEL: GateType.MOON,
    }

    KEY_TARGETS = set(KEY_TO_GATE.keys())

    def __init__(self):
        # Gemeinsames Spielbrett des Spiels.
        self.board = Board()

        # Liste aller teilnehmenden Spieler.
        self.players: list[Player] = []

        # Index des Spielers, der aktuell am Zug ist.
        self.current_player_index = 0

        # Speichert, ob in diesem Zug bereits geschoben wurde.
        self.has_shifted = False

        # Speichert, ob sich der Spieler in diesem Zug bereits bewegt hat.
        self.has_moved = False

        # Speichert den letzten Schiebezug.
        # Damit kann ein direktes Zurückschieben verhindert werden.
        self.last_shift: tuple[int, Direction] | None = None

        # Aktivierte Schlüssel
        self.activated_keys: set[Target] = set()

        # Spielstatus.
        self.started = False
        self.finished = False
        self.winner: Player | None = None


    @staticmethod
    def _get_opposite_direction(direction: Direction) -> Direction:
        """
        Gibt die entgegengesetzte Richtung zurück.

        :param direction: Richtung, für die die Gegenrichtung bestimmt werden soll.
        :return: Entgegengesetzte Richtung.
        """
        opposite_directions = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST,
        }

        return opposite_directions[direction]


    def get_current_player(self) -> Player:
        """
        Gibt den Spieler zurück, der aktuell am Zug ist.

        :return: Aktuell aktiver Spieler.
        :raises ValueError: Wenn noch keine Spieler vorhanden sind.
        """

        # Ein Spiel ohne Spieler besitzt keinen aktiven Spieler.
        if not self.players:
            raise ValueError("Es befinden sich keine Spieler im Spiel.")

        return self.players[self.current_player_index]

    def add_player(self, name: str) -> None:
        """
        Fügt einen Spieler zum Spiel hinzu.

        :param name: Name des neuen Spielers.
        :raises ValueError: Wenn das Spiel bereits gestartet wurde.
        :raises ValueError: Wenn bereits vier Spieler teilnehmen.
        """

        if self.started:
            raise ValueError(
                "Nach Spielstart können keine Spieler mehr hinzugefügt werden."
            )

        if len(self.players) >= 4:
            raise ValueError(
                "Es können maximal vier Spieler teilnehmen."
            )

        start_positions = [
            (0, 0),
            (0, 6),
            (6, 6),
            (6, 0),
        ]

        row, column = start_positions[
            len(self.players)
        ]

        player = Player(
            name=name,
            row=row,
            column=column
        )

        self.players.append(player)

    def insert_spare_tile(self, index: int, direction: Direction) -> None:
        """
        Schiebt das freie Plättchen in das Spielbrett ein.

        Pro Zug darf nur einmal geschoben werden. Außerdem darf der
        unmittelbar vorherige Schiebezug nicht direkt rückgängig
        gemacht werden.

        :param index: Zeile oder Spalte, die verschoben werden soll.
        :param direction: Richtung, in die geschoben wird.
        :raises ValueError: Wenn in diesem Zug bereits geschoben wurde.
        :raises ValueError: Wenn der vorherige Schiebezug direkt rückgängig
                            gemacht werden soll.
        """

        self._ensure_game_active()

        # Pro Zug darf nur einmal geschoben werden.
        if self.has_shifted:
            raise ValueError(
                "Das Labyrinth wurde in diesem Zug bereits verschoben."
            )

        # Prüfen, ob es bereits einen vorherigen Schiebezug gibt.
        if self.last_shift is not None:
            last_index, last_direction = self.last_shift

            # Die Richtung bestimmen, die den vorherigen Zug
            # unmittelbar rückgängig machen würde.
            forbidden_direction = self._get_opposite_direction(
                last_direction
            )

            # Dieselbe Reihe bzw. Spalte darf nicht direkt
            # in die entgegengesetzte Richtung geschoben werden.
            if index == last_index and direction == forbidden_direction:
                raise ValueError(
                    "Der vorherige Schiebezug darf nicht direkt "
                    "rückgängig gemacht werden."
                )

        # Das Spielbrett verschieben.
        self.board.insert_spare_tile(
            index,
            direction
        )

        # Spieler auf der betroffenen Reihe oder Spalte mitverschieben.
        self._move_players_after_shift(
            index,
            direction
        )

        # Aktuellen Schiebezug für den nächsten Spieler speichern.
        self.last_shift = (
            index,
            direction
        )

        # Merken, dass in diesem Zug bereits geschoben wurde.
        self.has_shifted = True


    def _move_players_after_shift(self, index: int, direction: Direction) -> None:
        """
        Verschiebt alle Spieler mit der betroffenen Reihe bzw. Spalte.

        Wird ein Spieler durch das Verschieben aus dem Spielbrett
        herausgeschoben, erscheint er auf der gegenüberliegenden Seite
        auf der neu eingeschobenen Kachel.

        Nur in diesem Fall werden die Effekte der neuen Kachel ausgelöst,
        da der Spieler bei einer normalen Verschiebung auf seiner bisherigen
        Kachel stehen bleibt.

        :param index: Verschobene Reihe oder Spalte.
        :param direction: Richtung der Verschiebung.
        """

        for player in self.players:

            # Merkt, ob der Spieler tatsächlich über den Rand
            # auf die gegenüberliegende Seite versetzt wurde.
            was_pushed_out = False

            # Einschieben von links:
            # Die Reihe bewegt sich nach rechts.
            if (
                    direction == Direction.EAST
                    and player.row == index
            ):
                # Spieler am rechten Rand wird herausgeschoben
                # und erscheint links auf der neuen Kachel.
                if player.column == self.board.SIZE - 1:
                    was_pushed_out = True

                player.column = (
                                        player.column + 1
                                ) % self.board.SIZE

            # Einschieben von rechts:
            # Die Reihe bewegt sich nach links.
            elif (
                    direction == Direction.WEST
                    and player.row == index
            ):
                # Spieler am linken Rand wird herausgeschoben
                # und erscheint rechts auf der neuen Kachel.
                if player.column == 0:
                    was_pushed_out = True

                player.column = (
                                        player.column - 1
                                ) % self.board.SIZE

            # Einschieben von oben:
            # Die Spalte bewegt sich nach unten.
            elif (
                    direction == Direction.SOUTH
                    and player.column == index
            ):
                # Spieler am unteren Rand wird herausgeschoben
                # und erscheint oben auf der neuen Kachel.
                if player.row == self.board.SIZE - 1:
                    was_pushed_out = True

                player.row = (
                                     player.row + 1
                             ) % self.board.SIZE

            # Einschieben von unten:
            # Die Spalte bewegt sich nach oben.
            elif (
                    direction == Direction.NORTH
                    and player.column == index
            ):
                # Spieler am oberen Rand wird herausgeschoben
                # und erscheint unten auf der neuen Kachel.
                if player.row == 0:
                    was_pushed_out = True

                player.row = (
                                     player.row - 1
                             ) % self.board.SIZE

            # Nur ein tatsächlich herausgeschobener Spieler
            # landet auf einer anderen Kachel.
            if was_pushed_out:
                self._handle_tile_effects(player)

                # Falls der Spieler dadurch auf seine Startposition
                # gelangt und bereits alle Ziele erfüllt hat,
                # kann auch das Verschieben das Spiel beenden.
                self._check_winner(player)


    def move_player(self, player: Player, target_row: int, target_column: int) -> None:
        """
        Bewegt einen Spieler auf ein erreichbares Feld des Spielbretts.

        Vor der Bewegung muss das Labyrinth verschoben worden sein.
        Noch geschlossene Tore werden bei der Wegfindung als
        nicht betretbare Felder behandelt.

        Nach erfolgreicher Bewegung werden automatisch Targets,
        Schlüssel und Portal-Effekte verarbeitet.

        :param player: Spieler, der bewegt werden soll.
        :param target_row: Zeile der gewünschten Zielposition.
        :param target_column: Spalte der gewünschten Zielposition.
        :raises ValueError: Wenn der Spieler nicht zum Spiel gehört.
        :raises ValueError: Wenn der Spieler nicht am Zug ist.
        :raises ValueError: Wenn noch nicht geschoben wurde.
        :raises ValueError: Wenn bereits eine Bewegung durchgeführt wurde.
        :raises ValueError: Wenn das Ziel ungültig oder nicht erreichbar ist.
        """

        self._ensure_game_active()

        if player not in self.players:
            raise ValueError(
                "Der Spieler gehört nicht zu diesem Spiel."
            )

        if player != self.get_current_player():
            raise ValueError(
                "Dieser Spieler ist aktuell nicht am Zug."
            )

        if not self.has_shifted:
            raise ValueError(
                "Vor der Bewegung muss zuerst das Labyrinth verschoben werden."
            )

        if self.has_moved:
            raise ValueError(
                "Der Spieler wurde in diesem Zug bereits bewegt."
            )

        if not self.board.is_valid_position(
            target_row,
            target_column
        ):
            raise ValueError(
                "Die Zielposition liegt außerhalb des Spielbretts."
            )

        # Alle Tore, deren jeweiliger Schlüssel noch nicht
        # aktiviert wurde, werden bei der Wegfindung gesperrt.
        blocked_positions = (
            self._get_locked_gate_positions()
        )

        # Alle aktuell tatsächlich erreichbaren Felder berechnen.
        reachable_positions = (
            self.board.get_reachable_positions(
                player.row,
                player.column,
                blocked_positions=blocked_positions
            )
        )

        if (
            target_row,
            target_column
        ) not in reachable_positions:
            raise ValueError(
                "Die Zielposition ist nicht erreichbar."
            )

        # Spieler auf die gewünschte Position bewegen.
        player.row = target_row
        player.column = target_column

        # Prüfen, ob dort ein persönliches Target
        # oder ein Schlüsselartefakt liegt.
        self._handle_tile_effects(player)

        # Prüfen, ob durch die Bewegung die Gewinnbedingung erfüllt wurde.
        self._check_winner(player)

        # Merken, dass in diesem Zug bereits bewegt wurde.
        self.has_moved = True


    def end_turn(self) -> None:
        """
        Beendet den aktuellen Zug und aktiviert den nächsten Spieler.

        Ein Zug darf erst beendet werden, nachdem das Labyrinth mindestens
        einmal verschoben wurde. Eine Spielerbewegung ist dagegen optional.

        :raises ValueError: Wenn noch keine Spieler vorhanden sind.
        :raises ValueError: Wenn das Labyrinth noch nicht verschoben wurde.
        """

        self._ensure_game_active()

        if not self.players:
            raise ValueError(
                "Es befinden sich keine Spieler im Spiel."
            )

        # Einschieben ist verpflichtend.
        if not self.has_shifted:
            raise ValueError(
                "Der Zug kann erst nach dem Verschieben des Labyrinths beendet werden."
            )

        # Zum nächsten Spieler wechseln.
        self.current_player_index = (
            self.current_player_index + 1
        ) % len(self.players)

        # Zugstatus für den neuen Spieler zurücksetzen.
        self.has_shifted = False
        self.has_moved = False

    def distribute_targets(self, targets_per_player: int) -> None:
        """
        Verteilt eine gewünschte Anzahl zufälliger Zielkarten
        auf alle teilnehmenden Spieler.

        Blattschlüssel und Mondschlüssel werden nicht verteilt,
        da sie als Schlüsselartefakte für die Tore dienen.

        :param targets_per_player: Anzahl der Zielkarten pro Spieler.
        :raises ValueError: Wenn weniger als zwei Spieler vorhanden sind.
        :raises ValueError: Wenn weniger als ein Target pro Spieler gewählt wurde.
        :raises ValueError: Wenn die gewünschte Anzahl nicht möglich ist.
        """

        if len(self.players) < 2:
            raise ValueError(
                "Targets können erst ab zwei Spielern verteilt werden."
            )

        if targets_per_player < 1:
            raise ValueError(
                "Jeder Spieler muss mindestens ein Target erhalten."
            )

        # Schlüsselartefakte aus den normalen Zielkarten ausschließen.
        available_targets = [
            target
            for target in Target
            if target not in self.KEY_TARGETS
        ]

        max_targets_per_player = (
            len(available_targets) // len(self.players)
        )

        if targets_per_player > max_targets_per_player:
            raise ValueError(
                f"Bei {len(self.players)} Spielern sind maximal "
                f"{max_targets_per_player} Targets pro Spieler möglich."
            )

        # Normale Zielkarten zufällig mischen.
        random.shuffle(available_targets)

        required_targets = (
            targets_per_player * len(self.players)
        )

        selected_targets = available_targets[:required_targets]

        # Alte Zielkarten zurücksetzen.
        for player in self.players:
            player.targets.clear()
            player.completed_targets.clear()

        # Zielkarten reihum verteilen.
        for index, target in enumerate(selected_targets):
            player_index = index % len(self.players)

            self.players[player_index].targets.append(
                target
            )

    def get_max_targets_per_player(self) -> int:
        """
        Ermittelt die maximal mögliche Anzahl an Zielkarten pro Spieler.

        Die beiden Schlüsselartefakte werden nicht als Zielkarten verteilt,
        da sie für die Tor-Mechanik benötigt werden.

        :return: Maximale Anzahl an Zielkarten pro Spieler.
        :raises ValueError: Wenn noch keine Spieler vorhanden sind.
        """

        if not self.players:
            raise ValueError(
                "Es befinden sich keine Spieler im Spiel."
            )

        # Nur normale Targets können als Zielkarten verteilt werden.
        available_targets = [
            target
            for target in Target
            if target not in self.KEY_TARGETS
        ]

        return len(available_targets) // len(self.players)


    def activate_key(self, target: Target) -> None:
        """
        Aktiviert ein Schlüsselartefakt global für das gesamte Spiel.

        Jeder Schlüssel öffnet genau das ihm zugeordnete Tor.

        :param target: Gefundenes Schlüsselartefakt.
        :raises ValueError: Wenn das Target kein Schlüssel ist.
        """

        if target not in self.KEY_TARGETS:
            raise ValueError(
                "Das angegebene Target ist kein Schlüsselartefakt."
            )

        self.activated_keys.add(target)

    def is_gate_open(self, gate_type: GateType) -> bool:
        """
        Prüft, ob ein bestimmtes Tor durch den zugehörigen
        Schlüssel bereits geöffnet wurde.

        :param gate_type: Zu prüfender Tortyp.
        :return: True, wenn der passende Schlüssel aktiviert wurde.
        """

        for key, mapped_gate in self.KEY_TO_GATE.items():
            if mapped_gate == gate_type:
                return key in self.activated_keys

        return False


    def _get_locked_gate_positions(self) -> set[tuple[int, int]]:
        """
        Ermittelt alle Tor-Kacheln, deren jeweiliger Schlüssel
        noch nicht aktiviert wurde.

        :return: Positionen aller aktuell gesperrten Tore.
        """

        locked_gates = set()

        for row in range(self.board.SIZE):
            for column in range(self.board.SIZE):

                tile = self.board.get_tile(
                    row,
                    column
                )

                # Normale Kacheln überspringen.
                if tile.gate is None:
                    continue

                # Dieses Tor ist nur dann gesperrt,
                # wenn sein eigener Schlüssel noch fehlt.
                if not self.is_gate_open(tile.gate):
                    locked_gates.add(
                        (row, column)
                    )

        return locked_gates

    def _get_portal_positions(self) -> list[tuple[int, int]]:
        """
        Ermittelt die Positionen aller Portal-Kacheln,
        die sich aktuell auf dem Spielbrett befinden.

        :return: Liste der Portalpositionen.
        """

        portal_positions = []

        for row in range(self.board.SIZE):
            for column in range(self.board.SIZE):

                tile = self.board.get_tile(
                    row,
                    column
                )

                if tile.portal:
                    portal_positions.append(
                        (row, column)
                    )

        return portal_positions

    def _use_portal(self, player: Player) -> None:
        """
        Teleportiert einen Spieler vom aktuellen Portal
        zum zweiten Portal auf dem Spielbrett.

        Eine Teleportation ist nur möglich, wenn sich beide
        Portal-Kacheln aktuell auf dem Spielbrett befinden.

        :param player: Spieler, der ein Portal betreten hat.
        """

        portal_positions = self._get_portal_positions()

        # Beide Portale müssen auf dem Spielbrett liegen.
        if len(portal_positions) != 2:
            return

        current_position = (
            player.row,
            player.column
        )

        # Das Portal bestimmen, auf dem der Spieler nicht steht.
        for portal_position in portal_positions:

            if portal_position != current_position:
                player.row, player.column = portal_position
                return

    def _handle_target(self, player: Player) -> None:
        """
        Verarbeitet das Target auf der aktuellen Position eines Spielers.

        Schlüsselartefakte werden global aktiviert.
        Normale Targets werden nur abgeschlossen, wenn sie dem
        aktuell gesuchten Target des Spielers entsprechen.

        :param player: Spieler, dessen aktuelle Position geprüft wird.
        """

        # Kachel bestimmen, auf der der Spieler aktuell steht.
        tile = self.board.get_tile(
            player.row,
            player.column
        )

        target = tile.target

        # Kachel besitzt kein Target.
        if target is None:
            return

        # Schlüsselartefakte werden unabhängig von den persönlichen
        # Zielkarten global aktiviert.
        if target in self.KEY_TARGETS:
            self.activate_key(target)
            return

        # Aktuelles persönliches Ziel des Spielers bestimmen.
        current_target = player.get_current_target()

        # Das Target zählt nur dann als gefunden, wenn es gerade
        # tatsächlich gesucht wird.
        if target == current_target:
            player.complete_current_target()

    def _handle_tile_effects(self, player: Player) -> None:
        """
        Verarbeitet alle Effekte der Kachel,
        auf der sich ein Spieler nach seiner Bewegung befindet.

        :param player: Spieler, dessen aktuelle Kachel verarbeitet wird.
        """

        tile = self.board.get_tile(
            player.row,
            player.column
        )

        # Zuerst mögliche Targets bzw. Schlüssel verarbeiten.
        self._handle_target(player)

        # Anschließend gegebenenfalls das Portal verwenden.
        if tile.portal:
            self._use_portal(player)


    def start_game(self, targets_per_player: int) -> None:
        """
        Startet das Spiel und verteilt die Zielkarten.

        Das Spiel kann nur einmal gestartet werden und benötigt
        mindestens zwei Spieler.

        :param targets_per_player: Anzahl persönlicher Targets pro Spieler.
        :raises ValueError: Wenn das Spiel bereits gestartet wurde.
        :raises ValueError: Wenn weniger als zwei Spieler vorhanden sind.
        :raises ValueError: Wenn die gewünschte Target-Anzahl ungültig ist.
        """

        if self.started:
            raise ValueError(
                "Das Spiel wurde bereits gestartet."
            )

        if len(self.players) < 2:
            raise ValueError(
                "Zum Starten werden mindestens zwei Spieler benötigt."
            )

        # Zielkarten entsprechend der gewählten Anzahl verteilen.
        self.distribute_targets(
            targets_per_player
        )

        # Der zuerst hinzugefügte Spieler beginnt.
        self.current_player_index = 0

        # Zugstatus zurücksetzen.
        self.has_shifted = False
        self.has_moved = False
        self.last_shift = None

        # Schlüsselzustand zurücksetzen.
        self.activated_keys.clear()

        # Spielstatus setzen.
        self.started = True
        self.finished = False
        self.winner = None


    def has_completed_all_targets(self, player: Player) -> bool:
        """
        Prüft, ob ein Spieler alle persönlichen Targets abgeschlossen hat.

        :param player: Zu prüfender Spieler.
        :return: True, wenn keine offenen Targets mehr vorhanden sind.
        """
        return len(player.targets) == 0

    def is_on_start_position(self, player: Player) -> bool:
        """
        Prüft, ob sich ein Spieler auf seinem eigenen Startfeld befindet.

        :param player: Zu prüfender Spieler.
        :return: True, wenn der Spieler auf seiner Startposition steht.
        """
        return (
                player.row == player.start_row
                and player.column == player.start_column
        )

    def _check_winner(self, player: Player) -> bool:
        """
        Prüft, ob ein Spieler die Gewinnbedingungen erfüllt.

        Ein Spieler gewinnt, wenn er alle persönlichen Targets
        abgeschlossen hat und anschließend auf sein eigenes
        Startfeld zurückgekehrt ist.

        :param player: Zu prüfender Spieler.
        :return: True, wenn der Spieler gewonnen hat.
        """

        if (
                self.has_completed_all_targets(player)
                and self.is_on_start_position(player)
        ):
            self.finished = True
            self.winner = player

            return True

        return False

    def _ensure_game_active(self) -> None:
        """
        Prüft, ob aktuell ein laufendes Spiel existiert.

        :raises ValueError: Wenn das Spiel noch nicht gestartet wurde.
        :raises ValueError: Wenn das Spiel bereits beendet wurde.
        """

        if not self.started:
            raise ValueError(
                "Das Spiel wurde noch nicht gestartet."
            )

        if self.finished:
            raise ValueError(
                "Das Spiel ist bereits beendet."
            )

    def rotate_spare_tile(self) -> None:
        """
        Dreht das freie Schiebeplättchen um 90 Grad im Uhrzeigersinn.

        Das Schiebeplättchen darf nur gedreht werden, bevor es
        in diesem Zug eingeschoben wurde.

        :raises ValueError: Wenn das Spiel nicht aktiv ist.
        :raises ValueError: Wenn in diesem Zug bereits geschoben wurde.
        """

        self._ensure_game_active()

        if self.has_shifted:
            raise ValueError(
                "Das Schiebeplättchen kann nach dem Einschieben "
                "nicht mehr gedreht werden."
            )

        self.board.spare_tile.rotate_clockwise()