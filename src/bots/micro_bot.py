import random
from typing import Literal

from sc2.ids.unit_typeid import UnitTypeId

from micro.factory.mine_micro import MineMicroMixin
from src.micro.barracks.marine_micro import MarineMicroMixin
from src.micro.barracks.maurader_micro import MarauderMicroMixin
from src.micro.barracks.reaper_micro import ReaperMicroMixin
from src.micro.factory.hellion_micro import HellionMicroMixin
from src.micro.factory.tank_micro import TankMicroMixin
from src.micro.starport.banshee_micro import BansheeMicroMixin
from src.micro.starport.medivac_micro import MedivacMicroMixin
from src.micro.starport.raven_micro import RavenMicroMixin
from src.micro.starport.viking_micro import VikingMicroMixin


## Bot to handle micro behaviors
## Desgined to be combined with the MacroBot
## and extended in the main bot class
class MicroBotMixin(
    ReaperMicroMixin,
    MarineMicroMixin,
    MarauderMicroMixin,
    TankMicroMixin,
    HellionMicroMixin,
    MineMicroMixin,
    RavenMicroMixin,
    VikingMicroMixin,
    MedivacMicroMixin,
    BansheeMicroMixin,
):
    MODE: Literal["attack", "defend"] = "defend"

    def set_micro_mode(self, mode: Literal["attack", "defend"]):
        self.MODE = mode

    async def fight(self):
        if self.MODE == "attack":
            self.MODE = "attack"
            for u in self.units.idle.filter(
                lambda unit: unit.type_id != UnitTypeId.SCV
                and unit.type_id != UnitTypeId.MULE
            ):
                possible_attack_locations = self.enemy_start_locations

                if self.all_enemy_units:
                    possible_attack_locations.append(self.all_enemy_units.center)

                u.attack(random.choice(possible_attack_locations))
        else:
            self.MODE = "defend"

    async def on_step_micro(self, iteration: int):
        # Barracks micro
        await self.reaper_micro(iteration, self.MODE)
        await self.marine_micro(iteration, self.MODE)
        await self.marauder_micro(iteration, self.MODE)
        # TODO ghost micro

        # Factory micro
        await self.tank_micro(iteration, self.MODE)
        await self.hellion_micro(iteration, self.MODE)
        await self.mine_micro(iteration, self.MODE)
        # TODO cyclone thor hellbat micro

        # Starport micro
        await self.raven_micro(iteration, self.MODE)
        await self.viking_micro(iteration, self.MODE)
        await self.medivac_micro(iteration, self.MODE)
        await self.banshee_micro(iteration, self.MODE)
        # TODO liberator bc micro

        # Worker micro
        # TODO worker micro
        await self.fight()
