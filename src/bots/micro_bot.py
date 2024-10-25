import random
from typing import Literal

from sc2.ids.unit_typeid import UnitTypeId

from src.micro.barracks.ghost_micro import GhostMicroMixin
from src.micro.barracks.marine_micro import MarineMicroMixin
from src.micro.barracks.maurader_micro import MarauderMicroMixin
from src.micro.barracks.reaper_micro import ReaperMicroMixin
from src.micro.cc_micro import CCMicroMixin
from src.micro.factory.cyclone_micro import CycloneMicroMixin
from src.micro.factory.hellion_micro import HellionMicroMixin
from src.micro.factory.mine_micro import MineMicroMixin
from src.micro.factory.tank_micro import TankMicroMixin
from src.micro.factory.thor_micro import ThorMicroMixin
from src.micro.starport.banshee_micro import BansheeMicroMixin
from src.micro.starport.battlecruiser_micro import BattleCruiserMicroMixin
from src.micro.starport.liberator_micro import LiberatorMicroMixin
from src.micro.starport.medivac_micro import MedivacMicroMixin
from src.micro.starport.raven_micro import RavenMicroMixin
from src.micro.starport.viking_micro import VikingMicroMixin


## Bot to handle micro behaviors
class MicroBotMixin(
    ReaperMicroMixin,
    MarineMicroMixin,
    MarauderMicroMixin,
    GhostMicroMixin,
    TankMicroMixin,
    HellionMicroMixin,
    MineMicroMixin,
    ThorMicroMixin,
    RavenMicroMixin,
    VikingMicroMixin,
    MedivacMicroMixin,
    BansheeMicroMixin,
    BattleCruiserMicroMixin,
    LiberatorMicroMixin,
    CycloneMicroMixin,
    CCMicroMixin,
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
        await self.fight()

        # CC micro
        await self.cc_micro(iteration, self.MODE)

        # Barracks micro
        await self.reaper_micro(iteration, self.MODE)
        await self.marine_micro(iteration, self.MODE)
        await self.marauder_micro(iteration, self.MODE)
        await self.ghost_micro(iteration, self.MODE)

        # Factory micro
        await self.tank_micro(iteration, self.MODE)
        await self.hellion_micro(iteration, self.MODE)
        await self.mine_micro(iteration, self.MODE)
        await self.thor_micro(iteration, self.MODE)
        await self.cyclone_micro(iteration, self.MODE)

        # Starport micro
        await self.raven_micro(iteration, self.MODE)
        await self.viking_micro(iteration, self.MODE)
        await self.medivac_micro(iteration, self.MODE)
        await self.banshee_micro(iteration, self.MODE)
        await self.battlecruiser_micro(iteration, self.MODE)
        await self.liberator_micro(iteration, self.MODE)

        # Worker micro
        # TODO worker micro
