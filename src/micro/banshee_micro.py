from typing import Literal

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units


class BansheeMicroMixin(BotAI):
    async def banshee_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        banshees: Units = self.units(UnitTypeId.BANSHEE)
        enemy_units = self.enemy_units.filter(lambda u: u.can_attack_air)
        enemy_workers = self.enemy_units(
            {UnitTypeId.SCV, UnitTypeId.DRONE, UnitTypeId.PROBE}
        )

        for banshee in banshees:
            if enemy_units.amount > 0 and enemy_units.closest_distance_to(banshee) < 7:
                banshee(AbilityId.BEHAVIOR_CLOAKON_BANSHEE)
            else:
                banshee(AbilityId.BEHAVIOR_CLOAKOFF_BANSHEE)

        for banshee in banshees.idle:
            if enemy_workers.amount == 0:
                banshee.move(self.enemy_start_locations[0])
            else:
                banshee.attack(enemy_workers.closest_to(banshee))
