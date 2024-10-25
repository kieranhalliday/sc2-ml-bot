from typing import Literal

from sc2.bot_ai import BotAI, Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.units import Units

from src.helpers import Helpers


class GhostMicroMixin(BotAI):
    async def ghost_micro(self, iteration: int, mode: Literal["attack", "defend"]):

        ghosts: Units = self.units(UnitTypeId.GHOST)

        priority_unit_types = [
            UnitTypeId.ULTRALISK,
            UnitTypeId.LURKER,
            UnitTypeId.BROODLORD,
            UnitTypeId.HIGHTEMPLAR,
            UnitTypeId.HYDRALISK,
            UnitTypeId.DARKTEMPLAR,
        ]

        priority_units = self.enemy_units.filter(lambda u: u in priority_unit_types)

        for g in ghosts:
            if self.enemy_units:
                if priority_units.filter(lambda u: g.target_in_range(u)):
                    g(AbilityId.SNIPE_SNIPE, priority_units.closest_to(g))

                # attack (or move towards) zerglings / banelings
                if g.weapon_cooldown <= self.client.game_step / 2:
                    enemies_in_range = self.enemy_units.filter(
                        lambda u: g.target_in_range(u)
                    )

                    # attack lowest hp enemy if any enemy is in range
                    if enemies_in_range:
                        # attack baneling first
                        enemies_to_attack = enemies_in_range

                        if (
                            self.enemy_race == Race.Protoss
                            and len(enemies_in_range) > 10
                        ):
                            g(AbilityId.EMP_EMP, enemies_in_range.center)

                        if enemies_in_range.of_type(UnitTypeId.BANELING).amount > 0:
                            enemies_to_attack = enemies_in_range.of_type(
                                UnitTypeId.BANELING
                            )

                        lowest_hp_enemy_in_range = min(
                            enemies_to_attack, key=lambda u: u.health
                        )
                        g.attack(lowest_hp_enemy_in_range)

                    # no enemy is in attack-range, so give attack command to closest instead
                    else:
                        closest_enemy = self.enemy_units.closest_to(g)
                        g.attack(closest_enemy)

                # move away from zergling / banelings
                else:

                    stutter_step_positions = Helpers.position_around_unit(
                        g,
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
                        lambda u: g.target_in_range(u, -0.5)
                    )

                    if stutter_step_positions and enemies_in_range:
                        retreat_position = max(
                            stutter_step_positions,
                            key=lambda x: x.distance_to(enemies_in_range.center)
                            - x.distance_to(g),
                        )
                        g.move(retreat_position)
                        # TODO: Lift ghosts into medivacs

                    else:
                        # print(
                        #     "No retreat positions detected for unit {} at {}.".format(
                        #         unit, unit.position.rounded
                        #     )
                        # )
                        pass
