# =============================================================================
# garage_utils.py - Libreria di supporto per gestione auto
#
# Contiene:
#   - Classe Car con attributi (brand, model, color, disabled)
#   - CarManager per gestione e persistenza su selected_cars.json
# =============================================================================

import json
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class Car:
    brand: str
    model: str
    color: str
    disabled: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Car":
        return cls(
            brand=d.get("brand", ""),
            model=d.get("model", ""),
            color=d.get("color", ""),
            disabled=bool(d.get("disabled", False))
        )

    def label(self) -> str:
        return f"{self.brand} {self.model}"

    @property
    def full_name(self) -> str:
        return f"{self.brand} {self.model}"

class CarManager:
    """Gestisce lista auto e persistenza su JSON."""

    def __init__(self, path: Path = Path("selected_cars.json")):
        self.path = path
        self.cars: list[Car] = self._load()

    def _load(self) -> list[Car]:
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
                return [Car.from_dict(c) for c in raw]
            except json.JSONDecodeError as e:
                print(f"Errore nel JSON: {e}")
        return []

    def save(self):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in self.cars], f, indent=2, ensure_ascii=False)

    def toggle_disabled(self, car: Car, value: bool):
        car.disabled = value
        self.save()

    def remove_car(self, car: Car):
        self.cars.remove(car)
        self.save()

    def validate_against_sections(self, num_sections: int) -> bool:
        """True se numero auto = numero sezioni garage."""
        return len(self.cars) == num_sections
