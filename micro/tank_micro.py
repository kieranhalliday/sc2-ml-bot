from typing import Literal
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.units import Units


class TankMicroMixin(BotAI):
    async def tank_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        tanks: Units = self.units(UnitTypeId.SIEGETANK) + self.units(
            UnitTypeId.SIEGETANKSIEGED
        )
        if mode == "defend":
            for tank in tanks.idle:
                tank(AbilityId.SIEGEMODE_SIEGEMODE)
        else:
            for tank in tanks:
                if (
                    len(self.enemy_units) > 0
                    and self.enemy_units.closest_distance_to(tank.position) < 14
                ) or (
                    len(self.enemy_structures) > 0
                    and self.enemy_structures.closest_distance_to(tank.position) < 14
                ):
                    tank(AbilityId.SIEGEMODE_SIEGEMODE)
                else:
                    tank(AbilityId.UNSIEGE_UNSIEGE)
