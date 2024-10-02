from typing import Literal

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units


class RavenMicroMixin(BotAI):
    async def raven_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        ravens: Units = self.units(UnitTypeId.RAVEN)

        priority_units = [
            UnitTypeId.SIEGETANKSIEGED,
            UnitTypeId.THOR,
            UnitTypeId.COLOSSUS,
            UnitTypeId.CARRIER,
            UnitTypeId.BATTLECRUISER,
        ]

        enemy_mechanicals = self.enemy_units.filter(
            lambda unit: unit.is_mechanical
            and unit.type_id is not UnitTypeId.SCV
            and unit.type_id is not UnitTypeId.PROBE
            and unit.type_id is not UnitTypeId.MULE
        )
        priority_enemy_mechanicals = enemy_mechanicals.filter(
            lambda unit: unit.type_id in priority_units
        )

        for raven in ravens.idle:
            if raven.energy >= 75:
                if priority_enemy_mechanicals.amount > 0:
                    raven(
                        AbilityId.EFFECT_INTERFERENCEMATRIX,
                        priority_enemy_mechanicals.closest_to(raven),
                    )
                    print(
                        f"Casting interference matrix on {priority_enemy_mechanicals.closest_to(raven)}"
                    )
                elif enemy_mechanicals.amount > 0:
                    raven(
                        AbilityId.EFFECT_INTERFERENCEMATRIX,
                        enemy_mechanicals.closest_to(raven),
                    )
                    print(
                        f"Casting interference matrix on {enemy_mechanicals.closest_to(raven)}"
                    )
            else:
                raven.move(self.start_location)
