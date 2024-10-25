import random
from typing import Literal

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units


class LiberatorMicroMixin(BotAI):
    async def liberator_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        libs: Units = self.units(UnitTypeId.LIBERATOR)
        enemy_workers = self.enemy_units(
            {UnitTypeId.SCV, UnitTypeId.DRONE, UnitTypeId.PROBE}
        )

        for lib in libs.idle:
            if enemy_workers.amount == 0:
                lib(
                    AbilityId.MORPH_LIBERATORAAMODE,
                    enemy_workers.closest_to(lib),
                )
                lib.move(random.choice(self.expansion_locations))
            else:
                lib(
                    AbilityId.MORPH_LIBERATORAGMODE,
                    enemy_workers.closest_to(lib),
                )
