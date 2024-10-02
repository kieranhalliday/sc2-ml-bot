from typing import Literal

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units


class MedivacMicroMixin(BotAI):
    async def medivac_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        medivacs: Units = self.units(UnitTypeId.MEDIVAC)
        hurt_bio_units: Units = self.units(
            {UnitTypeId.MARINE, UnitTypeId.MARAUDER, UnitTypeId.GHOST}
        ).filter(lambda m: m.health_percentage < 100)

        if hurt_bio_units.amount == 0:
            return

        for medivac in medivacs.idle:
            medivac.move(hurt_bio_units.random.position)
