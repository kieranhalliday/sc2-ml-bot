from typing import Literal

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units


class MineMicroMixin(BotAI):
    async def mine_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        mines: Units = self.units(UnitTypeId.WIDOWMINE) + self.units(
            UnitTypeId.WIDOWMINEBURROWED
        )
        if mode == "defend":
            for mine in mines.idle:
                mine(AbilityId.BURROWDOWN_WIDOWMINE)
        else:
            for mine in mines:
                if (
                    len(self.enemy_units) > 0
                    and self.enemy_units.closest_distance_to(mine.position) < 10
                ):
                    mine(AbilityId.BURROWDOWN_WIDOWMINE)
                else:
                    mine(AbilityId.BURROWUP_WIDOWMINE)
