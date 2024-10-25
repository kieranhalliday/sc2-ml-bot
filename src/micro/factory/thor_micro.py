import random
from typing import Literal

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units


class ThorMicroMixin(BotAI):
    async def thor_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        thors: Units = self.units(UnitTypeId.THOR)

        priority_unit_types = [
            UnitTypeId.SIEGETANKSIEGED,
            UnitTypeId.THOR,
            UnitTypeId.COLOSSUS,
            UnitTypeId.CARRIER,
            UnitTypeId.TEMPEST,
            UnitTypeId.BATTLECRUISER,
        ]

        priority_units = self.enemy_units.filter(lambda u: u in priority_unit_types)

        for thor in thors:
            thor(AbilityId.MORPH_THORHIGHIMPACTMODE)
            if self.enemy_units.amount > 0:
                if len(priority_units) > 0:
                    thor.attack(priority_units.closest_to(thor))
                else:
                    thor.attack(self.enemy_units.closest_to(thor))
            elif self.MODE == "attack":
                thor.attack(random.choice(self.enemy_start_locations))
            else:
                thor.move(random.choice(self.townhalls))
