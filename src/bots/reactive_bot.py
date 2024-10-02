from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit


# This is where all the triggers and responses will live
class ReactiveBotMixin(BotAI):
    async def on_unit_took_damage(self, unit: Unit, amount_damage_taken: float):
        if unit.is_structure and unit.health_percentage < 2:
            unit(AbilityId.CANCEL)
            return

        priority_repair_buildings = [
            UnitTypeId.PLANETARYFORTRESS,
            UnitTypeId.BUNKER,
            UnitTypeId.MISSILETURRET,
        ]

        available_workers = self.workers.filter(lambda worker: not worker.is_repairing)

        if not available_workers:
            return

        if unit.type_id in priority_repair_buildings and unit.health_percentage < 100:
            # Always pull lots of workers for priority buildings
            for worker in available_workers.closest_n_units(unit.position, 10):
                if worker is None:
                    break
                worker.repair(unit)

        elif unit.health_percentage < 50 and unit.is_mechanical:
            worker = available_workers.closest_to(unit.position)
            if worker is None or worker.distance_to(unit) > 20:
                return
            worker.repair(unit)

    async def on_enemy_unit_entered_vision(self, unit: Unit):
        idle_combat_units = self.units.filter(
            lambda u: unit.type_id is not UnitTypeId.SCV
        ).idle

        if unit.cloak:
            for detector in idle_combat_units.filter(lambda u: unit.is_detector):
                detector.move(unit)

        if unit.is_flying:
            for idle_unit in idle_combat_units.filter(lambda u: u.can_attack_air):
                idle_unit.attack(unit)

        else:
            for idle_unit in idle_combat_units.filter(lambda u: u.can_attack_ground):
                idle_unit.attack(unit)
