import random
from typing import Literal

from sc2.bot_ai import BotAI
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId

from src.helpers import Helpers


class CCMicroMixin(BotAI):
    async def cc_micro(self, iteration: int, mode: Literal["attack", "defend"]):

        max_minerals_left = 0
        for cc in self.townhalls:
            mfs = self.mineral_field.closer_than(10, cc)
            if mfs:
                minerals_left = sum(map(lambda mf: mf.mineral_contents, mfs))
                if minerals_left > max_minerals_left:
                    latest_cc = cc

            # Scan cloaked units
            for enemy_unit in self.enemy_units:
                closest_five_units = self.units.closest_n_units(
                    enemy_unit.position, 5
                ).filter(lambda unit: unit.distance_to(enemy_unit.position) <= 5)

                if enemy_unit.is_cloaked and len(closest_five_units) == 5:
                    cc(
                        AbilityId.SCANNERSWEEP_SCAN,
                        enemy_unit.position,
                        can_afford_check=True,
                    )

            # Drop mules
            mfs = self.mineral_field.closer_than(10, latest_cc)
            if mfs:
                mf = max(mfs, key=lambda x: x.mineral_contents)
                cc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf, can_afford_check=True)
