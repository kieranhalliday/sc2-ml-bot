import random
from typing import Literal

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units

from src.helpers import Helpers


class HellionMicroMixin(BotAI):
    async def hellion_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        hellions: Units = self.units(UnitTypeId.HELLION)

        for h in hellions:
            # move to range 15 of closest unit if reaper is below 20 hp and not regenerating
            enemyThreatsClose = self.enemy_units.filter(
                lambda x: x.can_attack_ground
            ).closer_than(
                15, h
            )  # threats that can attack the reaper
            if h.health_percentage < 2 / 5 and enemyThreatsClose.exists:
                retreatPoints = Helpers.neighbors8(
                    h.position, distance=2
                ) | Helpers.neighbors8(h.position, distance=4)
                # filter points that are pathable
                retreatPoints = {x for x in retreatPoints if self.in_pathing_grid(x)}
                if retreatPoints:
                    closestEnemy = enemyThreatsClose.closest_to(h)
                    retreatPoint = closestEnemy.position.furthest(retreatPoints)
                    h.move(retreatPoint)
                    continue  # continue for loop, dont execute any of the following

            # reaper is ready to attack, shoot nearest ground unit
            enemyGroundUnits = self.enemy_units.not_flying.closer_than(
                5, h
            )  # hardcoded attackrange of 5
            if h.weapon_cooldown == 0 and enemyGroundUnits.exists:
                enemyGroundUnits = enemyGroundUnits.sorted(lambda x: x.distance_to(h))
                closestEnemy = enemyGroundUnits[0]
                h.attack(closestEnemy)
                continue  # continue for loop, dont execute any of the following

            # move towards to max unit range if enemy is closer than 4
            enemyThreatsVeryClose = self.enemy_units.filter(
                lambda x: x.can_attack_ground
            ).closer_than(
                4.5, h
            )  # hardcoded attackrange minus 0.5
            # threats that can attack the reaper
            if h.weapon_cooldown != 0 and enemyThreatsVeryClose.exists:
                retreatPoints = Helpers.neighbors8(
                    h.position, distance=2
                ) | Helpers.neighbors8(h.position, distance=4)
                # filter points that are pathable by a reaper
                retreatPoints = {x for x in retreatPoints if self.in_pathing_grid(x)}
                if retreatPoints:
                    closestEnemy = enemyThreatsVeryClose.closest_to(h)
                    retreatPoint = max(
                        retreatPoints,
                        key=lambda x: x.distance_to(closestEnemy) - x.distance_to(h),
                    )
                    # retreatPoint = closestEnemy.position.furthest(retreatPoints)
                    h.move(retreatPoint)
                    continue  # continue for loop, don't execute any of the following

            # move to nearest enemy ground unit/building because no enemy unit is closer than 5
            allEnemyGroundUnits = self.enemy_units.not_flying
            if allEnemyGroundUnits.exists:
                closestEnemy = allEnemyGroundUnits.closest_to(h)
                h.move(closestEnemy)
                continue  # continue for loop, don't execute any of the following

            # move to random enemy start location if no enemy buildings have been seen
            h.move(random.choice(self.enemy_start_locations))
