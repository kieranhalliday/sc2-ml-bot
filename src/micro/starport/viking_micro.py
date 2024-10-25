from typing import Literal

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units

from src.helpers import Helpers


class VikingMicroMixin(BotAI):
    async def viking_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        vikings: Units = self.units(UnitTypeId.VIKINGFIGHTER) + self.units(
            UnitTypeId.VIKINGASSAULT
        )

        priority_unit_types = [
            UnitTypeId.RAVEN,
            UnitTypeId.BATTLECRUISER,
            UnitTypeId.CARRIER,
            UnitTypeId.TEMPEST,
            UnitTypeId.BROODLORD,
            UnitTypeId.COLOSSUS,
        ]

        flying_units = self.enemy_units.filter(lambda unit: unit.is_flying)
        priority_flying_units = flying_units.filter(
            lambda unit: unit.type_id in priority_unit_types
        )

        for v in vikings.flying.idle:
            if v.weapon_cooldown == 0:
                if priority_flying_units.amount > 0:
                    v.attack(priority_flying_units.closest_to(v))
                elif flying_units.amount > 0:
                    v.attack(flying_units.closest_to(v))
            elif flying_units.amount > 0 and flying_units.closest_distance_to(v) < 9:
                stutter_step_positions = Helpers.position_around_unit(
                    v,
                    self.game_info.pathing_grid.width,
                    self.game_info.pathing_grid.height,
                    distance=4,
                )

                # filter in pathing grid
                stutter_step_positions = {
                    p for p in stutter_step_positions if self.in_pathing_grid(p)
                }

                # find position furthest away from enemies and closest to unit
                enemies_in_range = self.enemy_units.filter(
                    lambda u: v.target_in_range(u, -0.5)
                )

                if stutter_step_positions and enemies_in_range:
                    retreat_position = max(
                        stutter_step_positions,
                        key=lambda x: x.distance_to(enemies_in_range.center)
                        - x.distance_to(v),
                    )
                    v.move(retreat_position)

            if len(flying_units) == 0 and self.enemy_units.amount > 0:
                v(AbilityId.MORPH_VIKINGASSAULTMODE)
            else:
                v(AbilityId.MORPH_VIKINGFIGHTERMODE)
