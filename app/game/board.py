import random

from app.game.enums import TileType, Direction, GateType
from app.game.tile import Tile
from app.game.target import Target

MOVABLE_CORNERS = 15
MOVABLE_T_JUNCTION = 6
MOVABLE_STRAIGHT = 11
MOVABLE_CROSS = 2

class Board:
    SIZE = 7

    def __init__(self):
        # Zunächst wird ein leeres 7x7-Spielbrett erzeugt.
        self.tiles: list[list[Tile | None]] = [
            [None for _ in range(self.SIZE)]
            for _ in range(self.SIZE)
        ]

        # Kachel, die sich aktuell außerhalb des Spielbretts befindet.
        self.spare_tile: Tile | None = None

        # Feste und bewegliche Kacheln erzeugen.
        self._place_fixed_tiles()
        self._place_movable_tiles()

        # Targets erst verteilen, nachdem das komplette Brett aufgebaut ist.
        self._distribute_targets()

    def get_tile(self, row: int, column: int) -> Tile:
        tile = self.tiles[row][column]

        if tile is None:
            raise ValueError("An dieser Position befindet sich keine Kachel.")

        return tile

    def _place_fixed_tiles(self) -> None:
        """
        Platziert die 16 festen Kacheln auf ihren festen Positionen.

        Die vier Eckkacheln dienen als Startfelder.
        Targets werden erst später unabhängig verteilt.
        """

        fixed_tiles = {
            # Obere Reihe
            (0, 0): Tile(
                TileType.CORNER,
                rotation=1,
                fixed=True
            ),
            (0, 2): Tile(
                TileType.T_JUNCTION,
                rotation=2,
                fixed=True
            ),
            (0, 4): Tile(
                TileType.T_JUNCTION,
                rotation=2,
                fixed=True
            ),
            (0, 6): Tile(
                TileType.CORNER,
                rotation=2,
                fixed=True
            ),

            # Reihe 2
            (2, 0): Tile(
                TileType.T_JUNCTION,
                rotation=1,
                fixed=True
            ),
            (2, 2): Tile(
                TileType.T_JUNCTION,
                rotation=1,
                fixed=True
            ),
            (2, 4): Tile(
                TileType.T_JUNCTION,
                rotation=2,
                fixed=True
            ),
            (2, 6): Tile(
                TileType.T_JUNCTION,
                rotation=3,
                fixed=True
            ),

            # Reihe 4
            (4, 0): Tile(
                TileType.T_JUNCTION,
                rotation=1,
                fixed=True
            ),
            (4, 2): Tile(
                TileType.T_JUNCTION,
                rotation=0,
                fixed=True
            ),
            (4, 4): Tile(
                TileType.T_JUNCTION,
                rotation=3,
                fixed=True
            ),
            (4, 6): Tile(
                TileType.T_JUNCTION,
                rotation=3,
                fixed=True
            ),

            # Untere Reihe
            (6, 0): Tile(
                TileType.CORNER,
                rotation=0,
                fixed=True
            ),
            (6, 2): Tile(
                TileType.T_JUNCTION,
                rotation=0,
                fixed=True
            ),
            (6, 4): Tile(
                TileType.T_JUNCTION,
                rotation=0,
                fixed=True
            ),
            (6, 6): Tile(
                TileType.CORNER,
                rotation=3,
                fixed=True
            ),
        }

        for (row, column), tile in fixed_tiles.items():
            self.tiles[row][column] = tile

    def _place_movable_tiles(self) -> None:
        """
        Erzeugt die 34 beweglichen Kacheln.

        Verteilung:
        - 15 Eckkacheln
        - 6 T-Kreuzungen
        - 11 gerade Kacheln
        - 2 Viererkreuzungen als Tore

        Zwei der Eckkacheln werden zufällig als Portale markiert.
        """

        # Normale bewegliche Kacheln erzeugen.
        corner_tiles = [
            Tile(TileType.CORNER)
            for _ in range(MOVABLE_CORNERS)
        ]

        t_tiles = [
            Tile(TileType.T_JUNCTION)
            for _ in range(MOVABLE_T_JUNCTION)
        ]

        straight_tiles = [
            Tile(TileType.STRAIGHT)
            for _ in range(MOVABLE_STRAIGHT)
        ]

        # Die beiden Viererkreuzungen sind immer Tore.
        gate_tiles = [
            Tile(
                TileType.CROSS,
                gate=GateType.LEAF
            ),
            Tile(
                TileType.CROSS,
                gate=GateType.MOON
            ),
        ]

        # Zwei zufällige Eckkacheln werden zu Portal-Kacheln.
        portal_tiles = random.sample(
            corner_tiles,
            2
        )

        for tile in portal_tiles:
            tile.portal = True

        # Alle beweglichen Kacheln zusammenführen.
        movable_tiles = (
                corner_tiles
                + t_tiles
                + straight_tiles
                + gate_tiles
        )

        # Jede bewegliche Kachel zufällig drehen.
        for tile in movable_tiles:
            tile.rotation = random.randint(0, 3)

        # Kacheln zufällig mischen.
        random.shuffle(movable_tiles)

        # Eine Kachel bleibt außerhalb des Bretts.
        self.spare_tile = movable_tiles.pop()

        # Die übrigen 33 Kacheln werden auf die freien Felder verteilt.
        for row in range(self.SIZE):
            for column in range(self.SIZE):
                if self.tiles[row][column] is None:
                    self.tiles[row][column] = movable_tiles.pop()

    def _distribute_targets(self) -> None:
        """
        Verteilt die 24 Targets zufällig auf feste und bewegliche Kacheln.

        Regeln:
        - 12 Targets liegen auf festen Kacheln.
        - 12 Targets liegen auf beweglichen Kacheln.
        - Startkacheln erhalten kein Target.
        - Gerade Kacheln erhalten kein Target.
        - Tor-Kacheln erhalten kein Target.
        - Portal-Kacheln erhalten kein Target.
        - Jede Kachel kann höchstens ein Target besitzen.
        """

        # Alle 24 Targets in zufälliger Reihenfolge.
        targets = list(Target)
        random.shuffle(targets)

        # ---------------------------------------------------------
        # Feste Kacheln
        # ---------------------------------------------------------

        # Die vier Eckfelder sind Startpositionen
        # und sollen kein Target erhalten.
        start_positions = {
            (0, 0),
            (0, 6),
            (6, 0),
            (6, 6),
        }

        fixed_target_tiles = []

        for row in range(self.SIZE):
            for column in range(self.SIZE):
                tile = self.tiles[row][column]

                if (
                        tile is not None
                        and tile.fixed
                        and (row, column) not in start_positions
                ):
                    fixed_target_tiles.append(tile)

        # Es müssen genau 12 geeignete feste Kacheln existieren.
        if len(fixed_target_tiles) != 12:
            raise ValueError(
                f"Es wurden {len(fixed_target_tiles)} feste "
                f"Target-Kacheln gefunden, erwartet wurden 12."
            )

        # Erste Hälfte der Targets auf feste Kacheln verteilen.
        for tile, target in zip(
                fixed_target_tiles,
                targets[:12]
        ):
            tile.target = target

        # ---------------------------------------------------------
        # Bewegliche Kacheln
        # ---------------------------------------------------------

        movable_target_tiles = []

        for row in range(self.SIZE):
            for column in range(self.SIZE):
                tile = self.tiles[row][column]

                if tile is None:
                    continue

                # Nur normale CORNER- und T_JUNCTION-Kacheln
                # dürfen ein Target erhalten.
                if (
                        not tile.fixed
                        and not tile.gate
                        and not tile.portal
                        and tile.tile_type in {
                    TileType.CORNER,
                    TileType.T_JUNCTION,
                }
                ):
                    movable_target_tiles.append(tile)

        # Das Schiebeplättchen gehört ebenfalls zum Kachelbestand.
        if (
                self.spare_tile is not None
                and not self.spare_tile.fixed
                and not self.spare_tile.gate
                and not self.spare_tile.portal
                and self.spare_tile.tile_type in {
            TileType.CORNER,
            TileType.T_JUNCTION,
        }
        ):
            movable_target_tiles.append(
                self.spare_tile
            )

        # Wir erwarten insgesamt 19 geeignete Kacheln:
        # 13 normale CORNER + 6 T_JUNCTION.
        if len(movable_target_tiles) < 12:
            raise ValueError(
                f"Zu wenige bewegliche Kacheln für Targets: "
                f"{len(movable_target_tiles)} vorhanden, 12 benötigt."
            )

        # Davon zufällig 12 auswählen.
        selected_tiles = random.sample(
            movable_target_tiles,
            12
        )

        # Zweite Hälfte der Targets verteilen.
        for tile, target in zip(
                selected_tiles,
                targets[12:]
        ):
            tile.target = target


    def print_board(self) -> None:
        for row in self.tiles:
            line = []

            for tile in row:
                if tile is None:
                    line.append("?")
                    continue

                symbol = {
                    TileType.STRAIGHT: "S",
                    TileType.CORNER: "C",
                    TileType.T_JUNCTION: "T",
                    TileType.CROSS: "X",
                }[tile.tile_type]

                if tile.fixed:
                    symbol = f"[{symbol}]"
                elif tile.gate:
                    symbol = f"G{symbol}"
                else:
                    symbol = f" {symbol} "

                line.append(symbol)

            print(" ".join(line))

        print()

        # Aktuelles Schiebeplättchen ausgeben
        if self.spare_tile is not None:
            spare_symbol = {
                TileType.STRAIGHT: "S",
                TileType.CORNER: "C",
                TileType.T_JUNCTION: "T",
                TileType.CROSS: "X",
            }[self.spare_tile.tile_type]

            if self.spare_tile.gate:
                spare_symbol = f"G{spare_symbol}"

            print(
                f"Spare Tile: {spare_symbol}, "
                f"Rotation: {self.spare_tile.rotation}"
            )


    def insert_spare_tile(self, index: int, direction: Direction) -> None:
        # Es darf nur an den beweglichen Reihen bzw. Spalten
        # 1, 3 und 5 eingeschoben werden.
        if index not in (1, 3, 5):
            raise ValueError(
                "Kacheln können nur bei Reihe/Spalte 1, 3 oder 5 eingeschoben werden."
            )

        # Sicherheitsprüfung: Es muss immer ein Schiebeplättchen vorhanden sein.
        if self.spare_tile is None:
            raise ValueError("Es gibt kein Schiebeplättchen.")

        # Wird nach Osten geschoben, kommt das Schiebeplättchen von links.
        if direction == Direction.EAST:
            self._shift_row_from_left(index)

        # Wird nach Westen geschoben, kommt das Schiebeplättchen von rechts.
        elif direction == Direction.WEST:
            self._shift_row_from_right(index)

        # Wird nach Süden geschoben, kommt das Schiebeplättchen von oben.
        elif direction == Direction.SOUTH:
            self._shift_column_from_top(index)

        # Wird nach Norden geschoben, kommt das Schiebeplättchen von unten.
        elif direction == Direction.NORTH:
            self._shift_column_from_bottom(index)

        else:
            raise ValueError("Ungültige Einschubrichtung.")

    def _shift_row_from_left(self, row: int) -> None:
        # Die Kachel ganz rechts wird aus dem Spielbrett herausgeschoben
        # und anschließend das neue Schiebeplättchen.
        new_spare_tile = self.tiles[row][self.SIZE - 1]

        # Alle Kacheln der Reihe um ein Feld nach rechts verschieben.
        # Rückwärts iterieren, damit keine Kachel überschrieben wird,
        # bevor sie kopiert wurde.
        for column in range(self.SIZE - 1, 0, -1):
            self.tiles[row][column] = self.tiles[row][column - 1]

        # Das bisherige Schiebeplättchen wird links eingesetzt.
        self.tiles[row][0] = self.spare_tile

        # Die rechts herausgeschobene Kachel ist nun das neue Schiebeplättchen.
        self.spare_tile = new_spare_tile

    def _shift_row_from_right(self, row: int) -> None:
        # Die Kachel ganz links wird aus dem Spielbrett herausgeschoben.
        new_spare_tile = self.tiles[row][0]

        # Alle Kacheln der Reihe um ein Feld nach links verschieben.
        for column in range(self.SIZE - 1):
            self.tiles[row][column] = self.tiles[row][column + 1]

        # Das bisherige Schiebeplättchen wird rechts eingesetzt.
        self.tiles[row][self.SIZE - 1] = self.spare_tile

        # Die links herausgeschobene Kachel wird zum neuen Schiebeplättchen.
        self.spare_tile = new_spare_tile

    def _shift_column_from_top(self, column: int) -> None:
        # Die unterste Kachel der Spalte wird herausgeschoben.
        new_spare_tile = self.tiles[self.SIZE - 1][column]

        # Alle Kacheln der Spalte um ein Feld nach unten verschieben.
        # Auch hier wird rückwärts iteriert, um Überschreiben zu vermeiden.
        for row in range(self.SIZE - 1, 0, -1):
            self.tiles[row][column] = self.tiles[row - 1][column]

        # Das bisherige Schiebeplättchen wird oben eingesetzt.
        self.tiles[0][column] = self.spare_tile

        # Die unten herausgeschobene Kachel wird zum neuen Schiebeplättchen.
        self.spare_tile = new_spare_tile

    def _shift_column_from_bottom(self, column: int) -> None:
        # Die oberste Kachel der Spalte wird herausgeschoben.
        new_spare_tile = self.tiles[0][column]

        # Alle Kacheln der Spalte um ein Feld nach oben verschieben.
        for row in range(self.SIZE - 1):
            self.tiles[row][column] = self.tiles[row + 1][column]

        # Das bisherige Schiebeplättchen wird unten eingesetzt.
        self.tiles[self.SIZE - 1][column] = self.spare_tile

        # Die oben herausgeschobene Kachel wird zum neuen Schiebeplättchen.
        self.spare_tile = new_spare_tile

    def is_valid_position(self, row: int, column: int) -> bool:
        """
        Prüft, ob sich eine Position innerhalb des Spielbretts befindet.

        :param row: Zeile der zu prüfenden Position.
        :param column: Spalte der zu prüfenden Position.
        :return: True, wenn die Position innerhalb des 7x7-Spielbretts liegt,
                 andernfalls False.
        """
        if 0 <= row < self.SIZE and 0 <= column < self.SIZE:
            return True
        else:
            return False

    def can_move(self, from_row: int, from_column: int, to_row: int, to_column: int) -> bool:
        """
        Prüft, ob zwischen zwei direkt benachbarten Kacheln ein begehbarer Weg besteht.

        Dafür müssen beide Kacheln an ihrer gemeinsamen Seite geöffnet sein.
        Diagonale Bewegungen sowie Bewegungen über mehrere Felder werden hier
        nicht geprüft.

        :param from_row: Zeile der Ausgangsposition.
        :param from_column: Spalte der Ausgangsposition.
        :param to_row: Zeile der Zielposition.
        :param to_column: Spalte der Zielposition.
        :return: True, wenn ein direkter Weg zwischen den beiden Kacheln besteht,
                 andernfalls False.
        """

        # Beide Positionen müssen innerhalb des Spielbretts liegen.
        if not self.is_valid_position(from_row, from_column):
            return False

        if not self.is_valid_position(to_row, to_column):
            return False

        # Differenz zwischen Ausgangs- und Zielposition bestimmen.
        row_difference = to_row - from_row
        column_difference = to_column - from_column

        # Nur direkt benachbarte Felder sind erlaubt.
        #
        # Beispiele:
        # (0, 1)  → rechts     = erlaubt
        # (1, 0)  → unten      = erlaubt
        # (1, 1)  → diagonal   = nicht erlaubt
        # (0, 2)  → zwei Felder entfernt = nicht erlaubt
        if abs(row_difference) + abs(column_difference) != 1:
            return False

        # Bewegungsrichtung sowie die entsprechende Gegenrichtung
        # auf der Zielkachel bestimmen.
        if row_difference == -1:
            # Bewegung nach Norden.
            direction = Direction.NORTH
            opposite_direction = Direction.SOUTH

        elif row_difference == 1:
            # Bewegung nach Süden.
            direction = Direction.SOUTH
            opposite_direction = Direction.NORTH

        elif column_difference == 1:
            # Bewegung nach Osten.
            direction = Direction.EAST
            opposite_direction = Direction.WEST

        else:
            # Bewegung nach Westen.
            direction = Direction.WEST
            opposite_direction = Direction.EAST

        # Ausgangs- und Zielkachel vom Spielbrett holen.
        current_tile = self.get_tile(
            from_row,
            from_column
        )

        target_tile = self.get_tile(
            to_row,
            to_column
        )

        # Ein Weg besteht nur dann, wenn:
        #
        # 1. die Ausgangskachel in Bewegungsrichtung geöffnet ist
        # UND
        # 2. die Zielkachel in Gegenrichtung geöffnet ist.
        if direction in current_tile.get_openings() and opposite_direction in target_tile.get_openings():
            return True
        else:
            return False


    def get_reachable_positions(self, start_row: int, start_column: int,
                                blocked_positions: set[tuple[int, int]] | None = None) -> set[tuple[int, int]]:
        """
        Ermittelt alle Felder, die von einer Startposition aus erreichbar sind.

        Optional können Positionen angegeben werden, die während der
        Wegfindung nicht betreten werden dürfen. Dies wird beispielsweise
        für noch geschlossene Tore verwendet.

        :param start_row: Zeile der Startposition.
        :param start_column: Spalte der Startposition.
        :param blocked_positions: Optional gesperrte Positionen.
        :return: Menge aller erreichbaren Positionen als (Zeile, Spalte).
        :raises ValueError: Wenn die Startposition außerhalb des Spielbretts liegt.
        """

        if not self.is_valid_position(
            start_row,
            start_column
        ):
            raise ValueError("Ungültige Startposition.")

        # Falls keine gesperrten Positionen angegeben wurden,
        # wird mit einer leeren Menge gearbeitet.
        if blocked_positions is None:
            blocked_positions = set()

        visited = {
            (start_row, start_column)
        }

        queue = [
            (start_row, start_column)
        ]

        while queue:
            current_row, current_column = queue.pop(0)

            neighbours = [
                (current_row - 1, current_column),  # Norden
                (current_row + 1, current_column),  # Süden
                (current_row, current_column + 1),  # Osten
                (current_row, current_column - 1),  # Westen
            ]

            for neighbour_row, neighbour_column in neighbours:

                # Bereits besuchte Positionen müssen nicht erneut
                # untersucht werden.
                if (
                    neighbour_row,
                    neighbour_column
                ) in visited:
                    continue

                # Gesperrte Felder dürfen nicht betreten werden.
                if (
                    neighbour_row,
                    neighbour_column
                ) in blocked_positions:
                    continue

                if self.can_move(
                    current_row,
                    current_column,
                    neighbour_row,
                    neighbour_column
                ):
                    visited.add(
                        (neighbour_row, neighbour_column)
                    )

                    queue.append(
                        (neighbour_row, neighbour_column)
                    )

        return visited