from dataclasses import dataclass, field

import unrealsdk
from mods_base import KeybindType, get_pc, keybind


@dataclass
class TPFastTravel:
    name: str  # "Teleport Between Fast Travel Stations"
    station_class: str  # "FastTravelStation"

    last_travel_index: int = field(init=False, default=0)
    cached_travel_names: list[str] = field(init=False, default_factory=lambda: ["DUMMY"])

    keybind: KeybindType = field(init=False)

    def __post_init__(self) -> None:
        self.keybind = keybind(self.name, None, callback=self.tp_next)

    def tp_next(self) -> None:
        """Teleports to the next travel station."""

        # Get the list of all station names in the world
        current_travels: list[str] = []
        for obj in unrealsdk.find_all(self.station_class):
            if (travel_def := obj.TravelDefinition) is None:
                continue
            current_travels.append(travel_def.Name)

        # If the current station is not in the list then we must have changed worlds
        if self.cached_travel_names[self.last_travel_index] not in current_travels:
            # Set to -1 so that it advances to the first one
            self.last_travel_index = -1
            self.cached_travel_names = current_travels

        if not self.cached_travel_names:
            return

        self.last_travel_index = (self.last_travel_index + 1) % len(self.cached_travel_names)
        get_pc().TeleportPlayerToStation(self.cached_travel_names[self.last_travel_index])


tp_fast_travel = TPFastTravel("Teleport Between Fast Travel Stations", "FastTravelStation")
tp_level_transition = TPFastTravel("Teleport Between Level Transitions", "LevelTravelStation")
