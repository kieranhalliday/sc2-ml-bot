import math
import pickle
import random
import time

import cv2
import numpy as np
from sc2.bot_ai import BotAI  # parent class we inherit from
from sc2.bot_ai import Race
from sc2.game_state import GameState
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit

import src.constants as constants
from src.actions import Actions, bot_actions

SAVE_REPLAY = True

INF_WEAPONS_LEVEL = 0
INF_ARMOUR_LEVEL = 0
VEHICLE_WEAPONS_LEVEL = 0
VEHICLE_ARMOUR_LEVEL = 0
SHIPS_WEAPONS_LEVEL = 0


## Bot to handle machine learning predictions, actions and rewards
class ActionHandler(BotAI):  # inhereits from BotAI (part of BurnySC2)

    micro_mode = "defend"

    async def handle_depot_height(self):
        # Raise depos when enemies are nearby
        for depo in self.structures(UnitTypeId.SUPPLYDEPOTLOWERED).ready:
            for unit in self.enemy_units:
                if unit.position.to2.distance_to(depo.position.to2) < 10:
                    depo(AbilityId.MORPH_SUPPLYDEPOT_RAISE)

        # Lower depos when no enemies are nearby
        for depo in self.structures(UnitTypeId.SUPPLYDEPOT).ready:
            for unit in self.enemy_units:
                if unit.position.to2.distance_to(depo.position.to2) < 15:
                    break
            else:
                depo(AbilityId.MORPH_SUPPLYDEPOT_LOWER)

    async def land_flying_buildings_with_add_on_space(self):
        # Don't land too close to a different add on position unless told to
        for structure in (
            self.structures(UnitTypeId.BARRACKSFLYING).idle
            + self.structures(UnitTypeId.FACTORYFLYING).idle
            + self.structures(UnitTypeId.STARPORTFLYING).idle
        ):
            new_position = await self.find_placement(
                UnitTypeId.BARRACKS,
                structure.position,
                addon_place=True,
                max_distance=20,
            )
            if new_position is not None and (
                len(self.structures({UnitTypeId.REACTOR, UnitTypeId.TECHLAB})) == 0
                or new_position.distance_to_closest(
                    map(
                        lambda addon: addon.add_on_land_position,
                        self.structures({UnitTypeId.REACTOR, UnitTypeId.TECHLAB}),
                    )
                )
                > 3
            ):
                structure(
                    AbilityId.LAND,
                    new_position,
                )

    async def handle_chosen_action(
        self, iteration: int
    ):  # on_step is a method that is called every step of the game.
        no_action = True
        while no_action:
            try:
                with open("data/state_rwd_action.pkl", "rb") as f:
                    state_rwd_action = pickle.load(f)

                    if state_rwd_action["action"] is None:
                        no_action = True
                    else:
                        no_action = False
            except:
                pass

        await self.distribute_workers()  # put idle workers back to work
        await self.handle_depot_height()  # raise depots when enemy units nearby
        await self.land_flying_buildings_with_add_on_space()  # Land flying buildings

        action = state_rwd_action["action"]
        reward = state_rwd_action["reward"] or 0

        max_minerals_left = 0

        latest_cc = None
        for cc in self.townhalls:
            mfs = self.mineral_field.closer_than(10, cc)
            if mfs:
                minerals_left = sum(map(lambda mf: mf.mineral_contents, mfs))
                if minerals_left > max_minerals_left:
                    latest_cc = cc

        if latest_cc is None and self.townhalls:
            latest_cc == random.choice(self.townhalls)

        try:
            # TODO:
            # Add more information to observation
            # Punish on unit death and structure destroyed: game_state.dead_units
            # Reward killing enemy unit or structure: game_state.dead_units
            # Build units on non idle structure with reactor
            # Land flying buildings
            # Fusion core upgrades
            # Learn where to position structures
            # Cast spells
            # Swap add ons
            # Repair buildings
            # orbital actions
            # Prep bot to be called as exec file and zipped for competition and only ran once
            # react to events (reactive_bot.py)
            # Leaking thread? client_session: <aiohttp.client.ClientSession object at 0x32107b770>
            match bot_actions[action]:
                case Actions.DO_NOTHING:
                    # Small reward for saving minerals
                    if self.minerals < 500:
                        reward += 0.03

                # Build Structures
                case Actions.BUILD_SUPPLY_DEPOT:
                    if (
                        self.supply_left < 5 * self.townhalls.amount
                        and self.supply_cap < 200
                        and self.already_pending(UnitTypeId.SUPPLYDEPOT)
                        <= self.townhalls.amount - 1
                        and self.can_afford(UnitTypeId.SUPPLYDEPOT)
                    ):
                        depot_placement_positions = self.main_base_ramp.corner_depots

                        finished_depots = self.structures(
                            UnitTypeId.SUPPLYDEPOT
                        ) | self.structures(UnitTypeId.SUPPLYDEPOTLOWERED)

                        # Filter finish depot locations
                        if finished_depots:
                            depot_placement_positions = {
                                d
                                for d in depot_placement_positions
                                if finished_depots.closest_distance_to(d) > 1
                            }

                        if len(depot_placement_positions) > 0:
                            target_depot_location = depot_placement_positions.pop()
                            await self.build(
                                UnitTypeId.SUPPLYDEPOT, target_depot_location
                            )
                        else:
                            await self.build(UnitTypeId.SUPPLYDEPOT, latest_cc)

                            if self.supply_left > 15:
                                reward -= 0.03
                            else:
                                reward += 0.03
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.BUILD_GAS:
                    for cc in self.townhalls:
                        for geyser in self.vespene_geyser.closer_than(10, cc):
                            if not self.structures(UnitTypeId.ASSIMILATOR).closer_than(
                                2.0, geyser
                            ).exists and self.can_afford(UnitTypeId.ASSIMILATOR):
                                await self.build(UnitTypeId.ASSIMILATOR, geyser)
                                reward += 0.01
                            else:
                                # Penalty for choosing illegal action
                                reward -= 0.005

                case Actions.BUILD_CC:
                    if self.already_pending(
                        UnitTypeId.COMMANDCENTER
                    ) == 0 and self.can_afford(UnitTypeId.COMMANDCENTER):
                        await self.expand_now()
                        reward += 1
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.BUILD_BARRACKS:
                    if self.can_afford(UnitTypeId.BARRACKS):
                        if len(self.structures(UnitTypeId.BARRACKS)) == 0:
                            await self.build(
                                UnitTypeId.BARRACKS,
                                self.main_base_ramp.barracks_correct_placement,
                            )
                        else:
                            await self.build(UnitTypeId.BARRACKS, near=latest_cc)

                        # Punish more than 10 barracks
                        reward += 1 - 0.1 * len(self.structures(UnitTypeId.BARRACKS))
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.BUILD_GHOST_ACADEMY:
                    if self.can_afford(UnitTypeId.GHOSTACADEMY):
                        await self.build(UnitTypeId.GHOSTACADEMY, near=latest_cc)

                        # Punish more than 1 GA
                        reward += 0.5 - 0.5 * len(
                            self.structures(UnitTypeId.GHOSTACADEMY)
                        )
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.BUILD_FACTORY:
                    if self.can_afford(UnitTypeId.FACTORY):
                        await self.build(UnitTypeId.FACTORY, near=latest_cc)
                        # Punish more than 10 factories
                        reward += 1 - 0.1 * len(self.structures(UnitTypeId.FACTORY))
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.BUILD_STARPORT:
                    if self.can_afford(UnitTypeId.STARPORT):
                        await self.build(UnitTypeId.STARPORT, near=latest_cc)

                        # Punish more than 5 starports
                        reward += 0.5 - 0.1 * len(self.structures(UnitTypeId.STARPORT))
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.BUILD_EBAY:
                    if self.can_afford(UnitTypeId.ENGINEERINGBAY):
                        await self.build(
                            UnitTypeId.ENGINEERINGBAY,
                            near=latest_cc,
                        )
                        # Punish more than 2 ebays
                        reward += 0.25 - 0.125 * len(
                            self.structures(UnitTypeId.ENGINEERINGBAY)
                        )
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.BUILD_ARMORY:
                    if self.can_afford(UnitTypeId.ARMORY):
                        await self.build(UnitTypeId.ARMORY, near=latest_cc)

                        # Punish more than 2 armories
                        reward += 0.5 - 0.25 * len(self.structures(UnitTypeId.ARMORY))
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.BUILD_FUSION_CORE:
                    if self.can_afford(UnitTypeId.FUSIONCORE):
                        await self.build(UnitTypeId.FUSIONCORE, near=latest_cc)
                        # Punish more than 1 FC
                        reward += 0.5 - 0.5 * len(
                            self.structures(UnitTypeId.FUSIONCORE)
                        )
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.BUILD_BUNKER:
                    if self.can_afford(UnitTypeId.BUNKER):
                        await self.build(UnitTypeId.BUNKER, near=latest_cc)
                        # Aim for 1 bunker per base
                        reward += 0.25 * len(self.townhalls) - 0.25 * len(
                            self.structures(UnitTypeId.BUNKER)
                        )
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.BUILD_TURRET:
                    if self.can_afford(UnitTypeId.MISSILETURRET):
                        await self.build(UnitTypeId.MISSILETURRET, near=latest_cc)

                        # Aim for 2 turrets per base
                        reward += 0.5 * len(self.townhalls) - 0.25 * len(
                            self.structures(UnitTypeId.MISSILETURRET)
                        )
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.BUILD_SENSOR:
                    if self.can_afford(UnitTypeId.SENSORTOWER):
                        await self.build(UnitTypeId.SENSORTOWER, near=latest_cc)
                        # Aim for 1 sensor per base
                        reward += 0.25 * len(self.townhalls) - 0.25 * len(
                            self.structures(UnitTypeId.SENSORTOWER)
                        )
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.BUILD_ORBITAL:
                    ccs = self.structures(UnitTypeId.COMMANDCENTER)
                    if len(ccs) > 0:
                        cc = random.choice(ccs)
                        if cc.is_idle and self.can_afford(UnitTypeId.ORBITALCOMMAND):
                            cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND)
                            reward += 0.05

                case Actions.BUILD_PF:
                    ccs = self.structures(UnitTypeId.COMMANDCENTER)
                    if len(ccs) > 0:
                        if cc.is_idle and self.can_afford(UnitTypeId.PLANETARYFORTRESS):
                            cc(AbilityId.UPGRADETOPLANETARYFORTRESS_PLANETARYFORTRESS)
                            reward += 0.05

                # Build Add ons
                case Actions.BUILD_BARRACKS_TECH_LAB:
                    for b in self.structures(UnitTypeId.BARRACKS).idle:
                        if not b.has_add_on and not await self.can_place_single(
                            UnitTypeId.SUPPLYDEPOT, b.position.offset((2.5, -0.5))
                        ):
                            b(AbilityId.LIFT_BARRACKS)
                        else:
                            b(AbilityId.BUILD_TECHLAB, queue=True)
                            break

                case Actions.BUILD_FACTORY_TECH_LAB:
                    for f in self.structures(UnitTypeId.FACTORY).idle:
                        if not f.has_add_on and not await self.can_place_single(
                            UnitTypeId.SUPPLYDEPOT, f.position.offset((2.5, -0.5))
                        ):
                            f(AbilityId.LIFT_FACTORY)
                        else:
                            f(AbilityId.BUILD_TECHLAB, queue=True)

                case Actions.BUILD_STARPORT_TECH_LAB:
                    for s in self.structures(UnitTypeId.STARPORT).idle:
                        if not s.has_add_on and not await self.can_place_single(
                            UnitTypeId.SUPPLYDEPOT, s.position.offset((2.5, -0.5))
                        ):
                            s(AbilityId.LIFT_STARPORT)
                        else:
                            s(AbilityId.BUILD_TECHLAB, queue=True)

                case Actions.BUILD_BARRACKS_REACTOR:
                    for b in self.structures(UnitTypeId.BARRACKS).idle:
                        if not b.has_add_on and not await self.can_place_single(
                            UnitTypeId.SUPPLYDEPOT, b.position.offset((2.5, -0.5))
                        ):
                            b(AbilityId.LIFT_BARRACKS)
                        else:
                            b(AbilityId.BUILD_REACTOR, queue=True)
                            break

                case Actions.BUILD_FACTORY_REACTOR:
                    for f in self.structures(UnitTypeId.FACTORY).idle:
                        if not f.has_add_on and not await self.can_place_single(
                            UnitTypeId.SUPPLYDEPOT, f.position.offset((2.5, -0.5))
                        ):
                            f(AbilityId.LIFT_FACTORY)
                        else:
                            f(AbilityId.BUILD_REACTOR, queue=True)

                case Actions.BUILD_STARPORT_REACTOR:
                    for s in self.structures(UnitTypeId.STARPORT).idle:
                        if not s.has_add_on and not await self.can_place_single(
                            UnitTypeId.SUPPLYDEPOT, s.position.offset((2.5, -0.5))
                        ):
                            s(AbilityId.LIFT_STARPORT)
                        else:
                            s(AbilityId.BUILD_REACTOR, queue=True)

                # Upgrades
                case Actions.UPGRADE_INF_WEAPONS:
                    INF_ARMOUR_LEVEL = math.floor(
                        self.already_pending_upgrade(
                            UpgradeId.TERRANINFANTRYWEAPONSLEVEL1
                        )
                        + self.already_pending_upgrade(
                            UpgradeId.TERRANINFANTRYWEAPONSLEVEL2
                        )
                        + self.already_pending_upgrade(
                            UpgradeId.TERRANINFANTRYWEAPONSLEVEL3
                        )
                    )

                    if (
                        self.structures(UnitTypeId.ENGINEERINGBAY).idle
                        and INF_WEAPONS_LEVEL < 3
                    ):
                        ebay = self.structures(UnitTypeId.ENGINEERINGBAY).idle.first
                        bio_count = len(self.units(UnitTypeId.MARINE)) + len(
                            self.units(UnitTypeId.MARAUDER)
                        )

                        if INF_WEAPONS_LEVEL == 0:
                            ebay.research(
                                UpgradeId.TERRANINFANTRYWEAPONSLEVEL1,
                                can_afford_check=True,
                            )
                            reward += 0.002 * bio_count
                        elif INF_WEAPONS_LEVEL == 1:
                            ebay.research(
                                UpgradeId.TERRANINFANTRYWEAPONSLEVEL2,
                                can_afford_check=True,
                            )
                            reward += 0.004 * bio_count
                        elif INF_WEAPONS_LEVEL == 2:
                            ebay.research(
                                UpgradeId.TERRANINFANTRYWEAPONSLEVEL3,
                                can_afford_check=True,
                            )
                            reward += 0.006 * bio_count
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.UPGRADE_INF_ARMOUR:
                    INF_ARMOUR_LEVEL = math.floor(
                        self.already_pending_upgrade(
                            UpgradeId.TERRANINFANTRYARMORSLEVEL1
                        )
                        + self.already_pending_upgrade(
                            UpgradeId.TERRANINFANTRYARMORSLEVEL2
                        )
                        + self.already_pending_upgrade(
                            UpgradeId.TERRANINFANTRYARMORSLEVEL3
                        )
                    )

                    if (
                        self.structures(UnitTypeId.ENGINEERINGBAY).idle
                        and INF_ARMOUR_LEVEL < 3
                    ):
                        ebay = self.structures(UnitTypeId.ENGINEERINGBAY).idle.first
                        bio_count = len(self.units(UnitTypeId.MARINE)) + len(
                            self.units(UnitTypeId.MARAUDER)
                        )

                        if INF_ARMOUR_LEVEL == 0:
                            ebay.research(
                                UpgradeId.TERRANINFANTRYARMORSLEVEL1,
                                can_afford_check=True,
                            )
                            reward += 0.002 * bio_count
                        elif INF_ARMOUR_LEVEL == 1:
                            ebay.research(
                                UpgradeId.TERRANINFANTRYARMORSLEVEL2,
                                can_afford_check=True,
                            )
                            reward += 0.004 * bio_count
                        elif INF_ARMOUR_LEVEL == 2:
                            ebay.research(
                                UpgradeId.TERRANINFANTRYARMORSLEVEL3,
                                can_afford_check=True,
                            )
                            reward += 0.006 * bio_count
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.UPGRADE_VEHICLE_WEAPONS:
                    VEHICLE_WEAPONS_LEVEL = math.floor(
                        self.already_pending_upgrade(
                            UpgradeId.TERRANINFANTRYARMORSLEVEL1
                        )
                        + self.already_pending_upgrade(
                            UpgradeId.TERRANINFANTRYARMORSLEVEL2
                        )
                        + self.already_pending_upgrade(
                            UpgradeId.TERRANINFANTRYARMORSLEVEL3
                        )
                    )

                    if (
                        self.structures(UnitTypeId.ARMORY).idle
                        and VEHICLE_WEAPONS_LEVEL < 3
                    ):
                        armory = self.structures(UnitTypeId.ARMORY).idle.first
                        mech_count = (
                            len(self.units(UnitTypeId.HELLION))
                            + len(self.units(UnitTypeId.CYCLONE))
                            + len(self.units(UnitTypeId.SIEGETANK))
                            + len(self.units(UnitTypeId.THOR))
                        )

                        if VEHICLE_WEAPONS_LEVEL == 0:
                            armory.research(
                                UpgradeId.TERRANVEHICLEWEAPONSLEVEL1,
                                can_afford_check=True,
                            )
                            reward += 0.002 * mech_count
                        elif VEHICLE_WEAPONS_LEVEL == 1:
                            armory.research(
                                UpgradeId.TERRANVEHICLEWEAPONSLEVEL2,
                                can_afford_check=True,
                            )
                            reward += 0.004 * mech_count
                        elif VEHICLE_WEAPONS_LEVEL == 2:
                            armory.research(
                                UpgradeId.TERRANVEHICLEWEAPONSLEVEL3,
                                can_afford_check=True,
                            )
                            reward += 0.006 * mech_count
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005
                case Actions.UPGRADE_VEHICLE_ARMOUR:
                    VEHICLE_ARMOUR_LEVEL = math.floor(
                        self.already_pending_upgrade(
                            UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1
                        )
                        + self.already_pending_upgrade(
                            UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2
                        )
                        + self.already_pending_upgrade(
                            UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL3
                        )
                    )

                    if (
                        self.structures(UnitTypeId.ARMORY).idle
                        and VEHICLE_ARMOUR_LEVEL < 3
                    ):
                        armory = self.structures(UnitTypeId.ARMORY).idle.first
                        mech_count = (
                            len(self.units(UnitTypeId.HELLION))
                            + len(self.units(UnitTypeId.CYCLONE))
                            + len(self.units(UnitTypeId.SIEGETANK))
                            + len(self.units(UnitTypeId.THOR))
                            + len(self.units(UnitTypeId.VIKING))
                            + len(self.units(UnitTypeId.BATTLECRUISER))
                        )

                        if VEHICLE_ARMOUR_LEVEL == 0:
                            armory.research(
                                UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1,
                                can_afford_check=True,
                            )
                            reward += 0.002 * mech_count
                        elif VEHICLE_ARMOUR_LEVEL == 1:
                            armory.research(
                                UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2,
                                can_afford_check=True,
                            )
                            reward += 0.004 * mech_count
                        elif VEHICLE_ARMOUR_LEVEL == 2:
                            armory.research(
                                UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL3,
                                can_afford_check=True,
                            )
                            reward += 0.006 * mech_count
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005

                case Actions.UPGRADE_SHIP_WEAPONS:
                    SHIPS_WEAPONS_LEVEL = math.floor(
                        self.already_pending_upgrade(UpgradeId.TERRANSHIPWEAPONSLEVEL1)
                        + self.already_pending_upgrade(
                            UpgradeId.TERRANSHIPWEAPONSLEVEL2
                        )
                        + self.already_pending_upgrade(
                            UpgradeId.TERRANSHIPWEAPONSLEVEL3
                        )
                    )
                    if (
                        self.structures(UnitTypeId.ARMORY).idle
                        and SHIPS_WEAPONS_LEVEL < 3
                    ):
                        armory = self.structures(UnitTypeId.ARMORY).idle.first
                        mech_count = len(self.units(UnitTypeId.VIKING)) + len(
                            self.units(UnitTypeId.BATTLECRUISER)
                        )

                        if SHIPS_WEAPONS_LEVEL == 0:
                            armory.research(
                                UpgradeId.TERRANSHIPWEAPONSLEVEL1,
                                can_afford_check=True,
                            )
                            reward += 0.002 * mech_count
                        elif SHIPS_WEAPONS_LEVEL == 1:
                            armory.research(
                                UpgradeId.TERRANSHIPWEAPONSLEVEL1,
                                can_afford_check=True,
                            )
                            reward += 0.004 * mech_count
                        elif SHIPS_WEAPONS_LEVEL == 2:
                            armory.research(
                                UpgradeId.TERRANSHIPWEAPONSLEVEL1,
                                can_afford_check=True,
                            )
                            reward += 0.006 * mech_count
                    else:
                        # Penalty for choosing illegal action
                        reward -= 0.005
                case Actions.UPGRADE_BUILDING_ARMOUR:
                    if self.structures(
                        UnitTypeId.ENGINEERINGBAY
                    ).idle and not self.already_pending_upgrade(
                        UpgradeId.TERRANBUILDINGARMOR
                    ):
                        ebay = self.structures(UnitTypeId.ENGINEERINGBAY).idle.first

                        ebay.research(
                            UpgradeId.TERRANBUILDINGARMOR,
                            can_afford_check=True,
                        )
                        reward += 0.05
                    else:
                        reward -= 0.03
                case Actions.UPGRADE_HI_SEC:
                    if self.structures(
                        UnitTypeId.ENGINEERINGBAY
                    ).idle and not self.already_pending_upgrade(
                        UpgradeId.HISECAUTOTRACKING
                    ):
                        ebay = self.structures(UnitTypeId.ENGINEERINGBAY).idle.first

                        ebay.research(
                            UpgradeId.HISECAUTOTRACKING,
                            can_afford_check=True,
                        )
                        reward += 0.05
                    else:
                        reward -= 0.03

                case Actions.UPGRADE_STIM:
                    if self.structures(UnitTypeId.BARRACKSTECHLAB).idle:
                        tech_lab = self.structures(
                            UnitTypeId.BARRACKSTECHLAB
                        ).idle.first
                        if not self.already_pending(
                            AbilityId.BARRACKSTECHLABRESEARCH_STIMPACK
                        ):
                            tech_lab(
                                AbilityId.BARRACKSTECHLABRESEARCH_STIMPACK,
                                can_afford_check=True,
                            )
                            reward += 0.5

                case Actions.UPGRADE_COMBAT_SHIELDS:
                    if self.structures(UnitTypeId.BARRACKSTECHLAB).idle:
                        tech_lab = self.structures(
                            UnitTypeId.BARRACKSTECHLAB
                        ).idle.first
                        if not self.already_pending(AbilityId.RESEARCH_COMBATSHIELD):
                            tech_lab(
                                AbilityId.RESEARCH_COMBATSHIELD, can_afford_check=True
                            )
                            reward += 0.25

                case Actions.UPGRADE_CONCUSSIVE_SHELLS:
                    if self.structures(UnitTypeId.BARRACKSTECHLAB).idle:
                        tech_lab = self.structures(
                            UnitTypeId.BARRACKSTECHLAB
                        ).idle.first
                        if not self.already_pending(
                            AbilityId.RESEARCH_CONCUSSIVESHELLS
                        ):
                            tech_lab(
                                AbilityId.RESEARCH_CONCUSSIVESHELLS,
                                can_afford_check=True,
                            )
                            reward += 0.25

                case Actions.UPGRADE_PRE_IGNITER:
                    if self.structures(UnitTypeId.FACTORYTECHLAB).idle:
                        tech_lab = self.structures(UnitTypeId.FACTORYTECHLAB).idle.first
                        if not self.already_pending_upgrade(
                            UpgradeId.INFERNALPREIGNITERS
                        ):
                            tech_lab.research(
                                UpgradeId.INFERNALPREIGNITERS, can_afford_check=True
                            )
                            reward += 0.1

                case Actions.UPGRADE_HURRICANE_ENGINES:
                    if self.structures(UnitTypeId.FACTORYTECHLAB).idle:
                        tech_lab = self.structures(UnitTypeId.FACTORYTECHLAB).idle.first
                        if not self.already_pending_upgrade(
                            UpgradeId.HURRICANETHRUSTERS
                        ):
                            tech_lab.research(
                                UpgradeId.HURRICANETHRUSTERS, can_afford_check=True
                            )
                            reward += 0.1

                case Actions.UPGRADE_DRILLING_CLAWS:
                    if self.structures(UnitTypeId.FACTORYTECHLAB).idle:
                        tech_lab = self.structures(UnitTypeId.FACTORYTECHLAB).idle.first
                        if not self.already_pending_upgrade(UpgradeId.DRILLCLAWS):
                            tech_lab.research(
                                UpgradeId.DRILLCLAWS, can_afford_check=True
                            )
                            reward += 0.1

                case Actions.UPGRADE_SMART_SERVOS:
                    if self.structures(UnitTypeId.FACTORYTECHLAB).idle:
                        tech_lab = self.structures(UnitTypeId.FACTORYTECHLAB).idle.first
                        if not self.already_pending_upgrade(UpgradeId.SMARTSERVOS):
                            tech_lab.research(
                                UpgradeId.SMARTSERVOS, can_afford_check=True
                            )
                            reward += 0.1

                case Actions.UPGRADE_BANSHEE_CLOAK:
                    if self.structures(UnitTypeId.STARPORT).idle:
                        tech_lab = self.structures(
                            UnitTypeId.STARPORTTECHLAB
                        ).idle.first
                        if not self.already_pending_upgrade(UpgradeId.BANSHEECLOAK):
                            tech_lab.research(
                                UpgradeId.BANSHEECLOAK, can_afford_check=True
                            )
                            reward += 0.1
                case Actions.UPGRADE_HYPERFLIGHT:
                    if self.structures(UnitTypeId.STARPORT).idle:
                        tech_lab = self.structures(
                            UnitTypeId.STARPORTTECHLAB
                        ).idle.first
                        if not self.already_pending_upgrade(UpgradeId.BANSHEESPEED):
                            tech_lab.research(
                                UpgradeId.BANSHEESPEED, can_afford_check=True
                            )
                            reward += 0.1
                case Actions.UPGRADE_INTERFERENCE:
                    if self.structures(UnitTypeId.STARPORT).idle:
                        tech_lab = self.structures(
                            UnitTypeId.STARPORTTECHLAB
                        ).idle.first
                        if not self.already_pending_upgrade(
                            UpgradeId.INTERFERENCEMATRIX
                        ):
                            tech_lab.research(
                                UpgradeId.INTERFERENCEMATRIX, can_afford_check=True
                            )
                            reward += 0.25

                # Train Units
                case Actions.TRAIN_SCV:
                    for cc in self.townhalls:
                        if cc.is_idle and self.can_afford(UnitTypeId.SCV):
                            cc.train(UnitTypeId.SCV)

                        worker_count = len(self.workers.closer_than(10, cc))
                        # Aim for 22 scvs per base
                        reward += -1.1 * len(self.townhalls) + 0.1 * worker_count

                case Actions.TRAIN_MARINE:
                    for b in self.structures(UnitTypeId.BARRACKS).ready.idle:
                        if self.can_afford(UnitTypeId.MARINE):
                            b.train(UnitTypeId.MARINE)
                            reward += 0.05

                case Actions.TRAIN_REAPER:
                    for b in self.structures(UnitTypeId.BARRACKS).ready.idle:
                        if self.can_afford(UnitTypeId.REAPER):
                            b.train(UnitTypeId.REAPER)
                            reward += 0.01

                case Actions.TRAIN_MARAUDER:
                    for b in self.structures(UnitTypeId.BARRACKS).ready.idle:
                        if self.can_afford(UnitTypeId.MARAUDER):
                            b.train(UnitTypeId.MARAUDER)
                            reward += 0.05

                case Actions.TRAIN_MARAUDER:
                    for b in self.structures(UnitTypeId.BARRACKS).ready.idle:
                        if self.can_afford(UnitTypeId.MARAUDER):
                            b.train(UnitTypeId.MARAUDER)
                            reward += 0.05

                case Actions.TRAIN_GHOST:
                    for b in self.structures(UnitTypeId.BARRACKS).ready.idle:
                        if self.can_afford(UnitTypeId.GHOST):
                            b.train(UnitTypeId.GHOST)
                            reward += 0.1

                case Actions.TRAIN_HELLION:
                    for b in self.structures(UnitTypeId.FACTORY).ready.idle:
                        if self.can_afford(UnitTypeId.HELLION):
                            b.train(UnitTypeId.HELLION)
                            reward += 0.03

                case Actions.TRAIN_MINE:
                    for b in self.structures(UnitTypeId.FACTORY).ready.idle:
                        if self.can_afford(UnitTypeId.WIDOWMINE):
                            b.train(UnitTypeId.WIDOWMINE)
                            reward += 0.03

                case Actions.TRAIN_CYCLONE:
                    for b in self.structures(UnitTypeId.FACTORY).ready.idle:
                        if self.can_afford(UnitTypeId.CYCLONE):
                            b.train(UnitTypeId.CYCLONE)
                            reward += 0.02

                case Actions.TRAIN_TANK:
                    for b in self.structures(UnitTypeId.FACTORY).ready.idle:
                        if self.can_afford(UnitTypeId.SIEGETANK):
                            b.train(UnitTypeId.SIEGETANK)
                            reward += 0.05

                case Actions.TRAIN_THOR:
                    for b in self.structures(UnitTypeId.FACTORY).ready.idle:
                        if self.can_afford(UnitTypeId.THOR):
                            b.train(UnitTypeId.THOR)
                            reward += 0.03

                case Actions.TRAIN_VIKING:
                    for b in self.structures(UnitTypeId.STARPORT).ready.idle:
                        if self.can_afford(UnitTypeId.VIKING):
                            b.train(UnitTypeId.VIKING)
                            reward += 0.03

                case Actions.TRAIN_MEDIVAC:
                    for b in self.structures(UnitTypeId.STARPORT).ready.idle:
                        if self.can_afford(UnitTypeId.MEDIVAC):
                            b.train(UnitTypeId.MEDIVAC)
                            reward += 0.05

                case Actions.TRAIN_LIBERATOR:
                    for b in self.structures(UnitTypeId.STARPORT).ready.idle:
                        if self.can_afford(UnitTypeId.LIBERATOR):
                            b.train(UnitTypeId.LIBERATOR)
                            reward += 0.03

                case Actions.TRAIN_BANSHEE:
                    for b in self.structures(UnitTypeId.STARPORT).ready.idle:
                        if self.can_afford(UnitTypeId.BANSHEE):
                            b.train(UnitTypeId.BANSHEE)
                            reward += 0.02

                case Actions.TRAIN_RAVEN:
                    for b in self.structures(UnitTypeId.STARPORT).ready.idle:
                        if self.can_afford(UnitTypeId.RAVEN):
                            b.train(UnitTypeId.RAVEN)
                            reward += 0.02

                case Actions.TRAIN_BC:
                    for b in self.structures(UnitTypeId.STARPORT).ready.idle:
                        if self.can_afford(UnitTypeId.BATTLECRUISER):
                            b.train(UnitTypeId.BATTLECRUISER)
                            reward += 0.03

                # Scout
                case Actions.SCOUT:
                    # are there any idle scvs:
                    try:
                        self.last_sent
                    except:
                        self.last_sent = 0

                    # if self.last_sent doesnt exist yet:
                    if (iteration - self.last_sent) > 200:
                        scv = random.choice(self.units(UnitTypeId.SCV))
                        scv.move(self.enemy_start_locations[0])
                        self.last_sent = iteration

                # Attack (known buildings, units, then enemy base)
                case Actions.ATTACK:
                    self.micro_mode = "attack"

                case Actions.DEFEND:
                    self.micro_mode = "defend"

                # case _:
        except Exception as e:
            reward -= 1
            # print("action")
            # print(action)
            print(e)

        # Prepare observations
        observation = np.zeros(
            (constants.MAX_MAP_HEIGHT, constants.MAX_MAP_WIDTH, 3), dtype=np.uint8
        )

        # draw the minerals:
        for mineral in self.mineral_field:
            pos = mineral.position
            c = [175, 255, 255]
            fraction = mineral.mineral_contents / 1800
            if mineral.is_visible:
                observation[math.ceil(pos.y)][math.ceil(pos.x)] = [
                    int(fraction * i) for i in c
                ]
            else:
                observation[math.ceil(pos.y)][math.ceil(pos.x)] = [20, 75, 50]

        # draw the enemy start location:
        for enemy_start_location in self.enemy_start_locations:
            pos = enemy_start_location
            c = [0, 0, 255]
            observation[math.ceil(pos.y)][math.ceil(pos.x)] = c

        # draw the enemy units:
        for enemy_unit in self.enemy_units:
            pos = enemy_unit.position
            c = [100, 0, 255]
            # get unit health fraction:
            fraction = (
                enemy_unit.health / enemy_unit.health_max
                if enemy_unit.health_max > 0
                else 0.0001
            )
            observation[math.ceil(pos.y)][math.ceil(pos.x)] = [
                int(fraction * i) for i in c
            ]

        # draw the enemy structures:
        for enemy_structure in self.enemy_structures:
            pos = enemy_structure.position
            c = [0, 100, 255]
            # get structure health fraction:
            fraction = (
                enemy_structure.health / enemy_structure.health_max
                if enemy_structure.health_max > 0
                else 0.0001
            )
            observation[math.ceil(pos.y)][math.ceil(pos.x)] = [
                int(fraction * i) for i in c
            ]

        # draw our structures:
        for our_structure in self.structures:
            # if it's a cc:
            if (
                our_structure.type_id == UnitTypeId.COMMANDCENTER
                or our_structure.type_id == UnitTypeId.ORBITALCOMMAND
                or our_structure.type_id == UnitTypeId.PLANETARYFORTRESS
            ):
                pos = our_structure.position
                c = [255, 255, 175]
                # get structure health fraction:
                fraction = (
                    our_structure.health / our_structure.health_max
                    if our_structure.health_max > 0
                    else 0.0001
                )
                observation[math.ceil(pos.y)][math.ceil(pos.x)] = [
                    int(fraction * i) for i in c
                ]

            else:
                pos = our_structure.position
                c = [0, 255, 175]
                # get structure health fraction:
                fraction = (
                    our_structure.health / our_structure.health_max
                    if our_structure.health_max > 0
                    else 0.0001
                )
                observation[math.ceil(pos.y)][math.ceil(pos.x)] = [
                    int(fraction * i) for i in c
                ]

        # draw the vespene geysers:
        for vespene in self.vespene_geyser:
            # draw these after buildings, since assimilators go over them.
            # tried to denote some way that assimilator was on top, couldnt
            # come up with anything. Tried by positions, but the positions arent identical. ie:
            # vesp position: (50.5, 63.5)
            # bldg positions: [(64.369873046875, 58.982421875), (52.85693359375, 51.593505859375),...]
            pos = vespene.position
            c = [255, 175, 255]
            fraction = vespene.vespene_contents / 2250

            if vespene.is_visible:
                observation[math.ceil(pos.y)][math.ceil(pos.x)] = [
                    int(fraction * i) for i in c
                ]
            else:
                observation[math.ceil(pos.y)][math.ceil(pos.x)] = [50, 20, 75]

        # draw our units:
        for our_unit in self.units:
            pos = our_unit.position
            c = [175, 255, 0]
            # get health:
            fraction = (
                our_unit.health / our_unit.health_max
                if our_unit.health_max > 0
                else 0.0001
            )
            observation[math.ceil(pos.y)][math.ceil(pos.x)] = [
                int(fraction * i) for i in c
            ]

        # Game state data
        # draw our minerals
        c = [255, 255, 255]
        observation[constants.MAX_MAP_HEIGHT - 1][constants.MAX_MAP_WIDTH - 1] = [
            min(int(self.minerals / 20), i) for i in c
        ]
        # draw our gas
        observation[constants.MAX_MAP_HEIGHT - 2][constants.MAX_MAP_WIDTH - 2] = [
            min(int(self.vespene / 20), i) for i in c
        ]
        # draw my supply
        observation[constants.MAX_MAP_HEIGHT - 3][constants.MAX_MAP_WIDTH - 3] = [
            self.supply_workers,
            self.supply_army,
            self.supply_cap,
        ]
        # draw enemy faction
        observation[constants.MAX_MAP_HEIGHT - 4][constants.MAX_MAP_WIDTH - 4] = [
            Race(self.enemy_race).value,
            Race(self.enemy_race).value,
            Race(self.enemy_race).value,
        ]

        # draw ebay upgrades x 8
        upgrade_ids = [
            UpgradeId.TERRANINFANTRYWEAPONSLEVEL1,
            UpgradeId.TERRANINFANTRYWEAPONSLEVEL2,
            UpgradeId.TERRANINFANTRYWEAPONSLEVEL3,
            UpgradeId.TERRANINFANTRYARMORSLEVEL1,
            UpgradeId.TERRANINFANTRYARMORSLEVEL2,
            UpgradeId.TERRANINFANTRYARMORSLEVEL3,
            UpgradeId.HISECAUTOTRACKING,
            UpgradeId.TERRANBUILDINGARMOR,
            UpgradeId.TERRANVEHICLEWEAPONSLEVEL1,
            UpgradeId.TERRANVEHICLEWEAPONSLEVEL2,
            UpgradeId.TERRANVEHICLEWEAPONSLEVEL1,
            UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1,
            UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2,
            UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL3,
            UpgradeId.TERRANSHIPWEAPONSLEVEL1,
            UpgradeId.TERRANSHIPWEAPONSLEVEL2,
            UpgradeId.TERRANSHIPWEAPONSLEVEL3,
            UpgradeId.STIMPACK,
            # Combat shield
            UpgradeId.SHIELDWALL,
            UpgradeId.PUNISHERGRENADES,
            # Infernal pre-igniter
            UpgradeId.HIGHCAPACITYBARRELS,
            UpgradeId.HURRICANETHRUSTERS,
            UpgradeId.DRILLCLAWS,
            UpgradeId.SMARTSERVOS,
            UpgradeId.BANSHEECLOAK,
            UpgradeId.BANSHEESPEED,
            UpgradeId.INTERFERENCEMATRIX,
        ]
        for index, upgrade_id in enumerate(upgrade_ids):
            observation[constants.MAX_MAP_HEIGHT - 5 - index][
                constants.MAX_MAP_WIDTH - 5 - index
            ] = [int(self.already_pending_upgrade(upgrade_id) * val) for val in c]

        # show observation with opencv, resized to be larger:
        # horizontal flip:
        # Uncomment to show observations on screen
        # cv2.imshow(
        #     "observation",
        #     cv2.flip(
        #         cv2.resize(
        #             observation, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST
        #         ),
        #         0,
        #     ),
        # )
        # cv2.waitKey(1)

        if SAVE_REPLAY:
            # save observation image into "replays dir"
            cv2.imwrite(f"replays/{int(time.time())}-{iteration}.png", observation)

        # Reward logic
        # print("Dead Units")
        # print(list(GameState.dead_units))
        try:
            attack_count = 0
            # iterate through our marines:
            for m in self.units(UnitTypeId.MARINE):
                # if voidray is attacking and is in range of enemy unit:
                if m.is_attacking and m.target_in_range:
                    if self.enemy_units.closer_than(
                        8, m
                    ) or self.enemy_structures.closer_than(8, m):
                        # reward += 0.005 # original was 0.005, decent results, but let's 3x it.
                        reward += 0.015
                        attack_count += 1

        except Exception as e:
            print("reward", e)
            reward = 0

        if iteration % 100 == 0:
            print(f"Iter: {iteration}. RWD: {reward}.")

        # write the file:
        data = {
            "state": observation,
            "reward": reward,
            "action": None,
            "done": False,
        }  # empty action waiting for the next one!

        with open("data/state_rwd_action.pkl", "wb") as f:
            pickle.dump(data, f)

        return self.micro_mode
