from dataclasses import dataclass, field

from app.game.target import Target
from app.game.enums import CharacterType


@dataclass
class Player:
    name: str
    row: int
    column: int

    # Persönliche Startposition des Spielers.
    # Wird beim Erzeugen automatisch aus row/column übernommen.
    start_row: int = field(init=False)
    start_column: int = field(init=False)

    # Noch nicht abgeschlossene Zielkarten.
    targets: list[Target] = field(default_factory=list)

    # Bereits abgeschlossene Zielkarten.
    completed_targets: list[Target] = field(default_factory=list)

    # Charakter des Spielers
    character: CharacterType | None = None

    # Sonderfähigkeiten Zustand des Magiers
    ability_used_for_current_target: bool = False

    def __post_init__(self) -> None:
        """
        Speichert die ursprüngliche Spielerposition als Startposition.
        """
        self.start_row = self.row
        self.start_column = self.column

    def get_current_target(self) -> Target | None:
        """
        Gibt das aktuell zu suchende Target zurück.

        :return: Aktuelles Target oder None, wenn alle Targets
                 abgeschlossen wurden.
        """
        if not self.targets:
            return None

        return self.targets[0]

    def complete_current_target(self) -> Target:
        """
        Markiert das aktuelle Target als abgeschlossen.

        :return: Das abgeschlossene Target.
        :raises ValueError: Wenn kein offenes Target vorhanden ist.
        """
        if not self.targets:
            raise ValueError(
                "Der Spieler besitzt kein offenes Target."
            )

        completed_target = self.targets.pop(0)

        self.completed_targets.append(
            completed_target
        )

        # Der Magier darf seine Fähigkeit einmal für jedes neu gesuchte Target verwenden.
        self.ability_used_for_current_target = False

        return completed_target