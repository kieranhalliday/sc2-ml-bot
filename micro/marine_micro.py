from typing import Literal
from helpers import Helpers
from sc2.bot_ai import BotAI
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId


class MarineMicroMixin(BotAI):
    async def marine_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        if mode == "defend":
            for bunker in self.structures(UnitTypeId.BUNKER).filter(
                lambda b: b.cargo_left > 0
            ):
                for unit in self.units(UnitTypeId.MARINE).idle.closest_n_units(
                    bunker.position, 4
                ):
                    unit.smart(bunker)

        else:
            for bunker in self.structures(UnitTypeId.BUNKER):
                bunker(AbilityId.UNLOADALL_BUNKER)
            for unit in self.units(UnitTypeId.MARINE):
                if self.enemy_units:
                    # attack (or move towards) zerglings / banelings
                    if unit.weapon_cooldown <= self.client.game_step / 2:
                        enemies_in_range = self.enemy_units.filter(
                            lambda u: unit.target_in_range(u)
                        )

                        # attack lowest hp enemy if any enemy is in range
                        if enemies_in_range:
                            # Use stimpack
                            if (
                                self.already_pending_upgrade(UpgradeId.STIMPACK) == 1
                                and not unit.has_buff(BuffId.STIMPACK)
                                and unit.health > 10
                            ):
                                unit(AbilityId.EFFECT_STIM)

                            # attack baneling first
                            enemies_to_attack = enemies_in_range
                            if enemies_in_range.of_type(UnitTypeId.BANELING).amount > 0:
                                enemies_to_attack = enemies_in_range.of_type(
                                    UnitTypeId.BANELING
                                )

                            lowest_hp_enemy_in_range = min(
                                enemies_to_attack, key=lambda u: u.health
                            )
                            unit.attack(lowest_hp_enemy_in_range)

                        # no enemy is in attack-range, so give attack command to closest instead
                        else:
                            closest_enemy = self.enemy_units.closest_to(unit)
                            unit.attack(closest_enemy)

                    # move away from zergling / banelings
                    else:
                        stutter_step_positions = Helpers.position_around_unit(
                            unit,
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
                            lambda u: unit.target_in_range(u, -0.5)
                        )

                        if stutter_step_positions and enemies_in_range:
                            retreat_position = max(
                                stutter_step_positions,
                                key=lambda x: x.distance_to(enemies_in_range.center)
                                - x.distance_to(unit),
                            )
                            unit.move(retreat_position)

                        else:
                            # print(
                            #     "No retreat positions detected for unit {} at {}.".format(
                            #         unit, unit.position.rounded
                            #     )
                            # )
                            pass
