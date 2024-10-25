import random
from typing import Literal

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units

from src.helpers import Helpers


class CycloneMicroMixin(BotAI):
    async def cyclone_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        cyclones: Units = self.units(UnitTypeId.CYCLONE)

        for c in cyclones:
            # move to range 15 of closest unit if hellion is below 4/5 hp
            enemyThreatsClose = self.enemy_units.filter(
                lambda x: x.can_attack_ground
            ).closer_than(
                15, c
            )  # threats that can attack the hellion
            if c.health_percentage < 4 / 5 and enemyThreatsClose.exists:
                retreatPoints = Helpers.neighbors8(
                    c.position, distance=2
                ) | Helpers.neighbors8(c.position, distance=4)
                # filter points that are pathable
                retreatPoints = {x for x in retreatPoints if self.in_pathing_grid(x)}
                if retreatPoints:
                    closestEnemy = enemyThreatsClose.closest_to(c)
                    retreatPoint = closestEnemy.position.furthest(retreatPoints)
                    c.move(retreatPoint)
                    continue  # continue for loop, dont execute any of the following

            # hellion is ready to attack, shoot nearest ground unit
            enemyGroundUnits = self.enemy_units.not_flying.closer_than(
                6, c
            )  # hardcoded attackrange of 5
            if c.weapon_cooldown == 0 and enemyGroundUnits.exists:
                enemyGroundUnits = enemyGroundUnits.sorted(lambda x: x.distance_to(c))
                closestEnemy = enemyGroundUnits[0]
                c.attack(closestEnemy)
                continue  # continue for loop, dont execute any of the following

            # move towards to max unit range if enemy is closer than 4
            enemyThreatsVeryClose = self.enemy_units.filter(
                lambda x: x.can_attack_ground
            ).closer_than(
                5.5, c
            )  # hardcoded attackrange minus 0.5
            # threats that can attack the hellion
            if c.weapon_cooldown != 0 and enemyThreatsVeryClose.exists:
                retreatPoints = Helpers.neighbors8(
                    c.position, distance=2
                ) | Helpers.neighbors8(c.position, distance=4)
                # filter points that are pathable by a hellion
                retreatPoints = {x for x in retreatPoints if self.in_pathing_grid(x)}
                if retreatPoints:
                    closestEnemy = enemyThreatsVeryClose.closest_to(c)
                    retreatPoint = max(
                        retreatPoints,
                        key=lambda x: x.distance_to(closestEnemy) - x.distance_to(c),
                    )
                    # retreatPoint = closestEnemy.position.furthest(retreatPoints)
                    c.move(retreatPoint)
                    continue  # continue for loop, don't execute any of the following

            # move to nearest enemy ground unit/building because no enemy unit is closer than 5
            allEnemyGroundUnits = self.enemy_units.not_flying
            if allEnemyGroundUnits.exists:
                closestEnemy = allEnemyGroundUnits.closest_to(c)
                c.move(closestEnemy)
                continue  # continue for loop, don't execute any of the following

            # move to random enemy start location if no enemy buildings have been seen
            c.move(random.choice(self.enemy_start_locations))
