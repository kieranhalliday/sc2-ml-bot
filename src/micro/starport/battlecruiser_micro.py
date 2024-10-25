import random
from typing import Literal

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units


class BattleCruiserMicroMixin(BotAI):
    async def battlecruiser_micro(
        self, iteration: int, mode: Literal["attack", "defend"]
    ):
        bcs: Units = self.units(UnitTypeId.BATTLECRUISER)

        priority_unit_types = [
            UnitTypeId.SIEGETANKSIEGED,
            UnitTypeId.THOR,
            UnitTypeId.COLOSSUS,
            UnitTypeId.CARRIER,
            UnitTypeId.TEMPEST,
            UnitTypeId.BATTLECRUISER,
        ]

        priority_units = self.enemy_units.filter(lambda u: u in priority_unit_types)

        for bc in bcs:
            if bc.health_percentage < 20:
                bc(AbilityId.EFFECT_TACTICALJUMP, self.start_location)
            elif self.enemy_units.amount > 0:
                if len(priority_units) > 0:
                    bc(AbilityId.YAMATO_YAMATOGUN, priority_units.closest_to(bc))
                else:
                    bc(AbilityId.YAMATO_YAMATOGUN, self.enemy_units.closest_to(bc))
            elif self.MODE == "attack":
                bc.attack(random.choice(self.enemy_start_locations))
            else:
                bc.move(random.choice(self.townhalls))
