from typing import Literal

from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units


class MedivacMicroMixin(BotAI):
    async def medivac_micro(self, iteration: int, mode: Literal["attack", "defend"]):
        medivacs: Units = self.units(UnitTypeId.MEDIVAC)
        hurt_ghosts = self.units(UnitTypeId.GHOST)
        hurt_bio_units: Units = self.units(
            {UnitTypeId.MARINE, UnitTypeId.MARAUDER}
        ).filter(lambda m: m.health_percentage < 100)

        # TODO:
        # Load medivacs with units
        # Empty full medivacs when safe.
        # Boost full medivacs out of danger.

        if hurt_bio_units.amount == 0:
            medivac.move(self.units(UnitTypeId.GHOST).closest_to(medivac))

        for medivac in medivacs.idle:
            if len(hurt_ghosts) > 0:
                medivac.move(hurt_ghosts.random)
            else:
                medivac.move(hurt_bio_units.random)
