from sc2.bot_ai import BotAI  # parent class we inherit from
from sc2.data import Difficulty, Race  # difficulty for bots, race for the 1 of 3 races
from sc2.main import (
    run_multiple_games,
    GameMatch,
)  # function that facilitates actually running the agents in games
from sc2.player import (
    Bot,
    Computer,
)  # wrapper for whether or not the agent is one of your bots, or a "computer" player
from sc2 import maps  # maps method for loading maps to play in.
from sc2.ids.unit_typeid import UnitTypeId
import random
import cv2
import math
import numpy as np
import sys
import pickle
import time
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from actions import Actions, bot_actions

SAVE_REPLAY = True

total_steps = 10000
steps_for_pun = np.linspace(0, 1, total_steps)
step_punishment = ((np.exp(steps_for_pun**3) / 10) - 0.1) * 10


class TerranBot(BotAI):  # inhereits from BotAI (part of BurnySC2)
    async def on_step(
        self, iteration: int
    ):  # on_step is a method that is called every step of the game.
        no_action = True
        while no_action:
            try:
                with open("state_rwd_action.pkl", "rb") as f:
                    state_rwd_action = pickle.load(f)

                    if state_rwd_action["action"] is None:
                        no_action = True
                    else:
                        no_action = False
            except:
                pass

        await self.distribute_workers()  # put idle workers back to work

        action = state_rwd_action["action"]
        reward = 0
        print(action)
        try:
            match bot_actions[action]:
                case Actions.DO_NOTHING:
                    print("No action")
                # Build Structures
                case Actions.BUILD_SUPPLY_DEPOT:
                    if (
                        self.supply_left < 4 * self.townhalls.amount
                        and self.supply_cap < 200
                        and self.already_pending(UnitTypeId.SUPPLYDEPOT)
                        <= self.townhalls.amount - 1
                        and self.can_afford(UnitTypeId.SUPPLYDEPOT)
                    ):
                        # TODO wall main ramp
                        await self.build(
                            UnitTypeId.SUPPLYDEPOT, near=random.choice(self.townhalls)
                        )

                case Actions.BUILD_GAS:
                    for cc in self.townhalls:
                        for geyser in self.vespene_geyser.closer_than(10, cc):
                            if not self.structures(UnitTypeId.ASSIMILATOR).closer_than(
                                2.0, geyser
                            ).exists and self.can_afford(UnitTypeId.ASSIMILATOR):
                                await self.build(UnitTypeId.ASSIMILATOR, geyser)
                case Actions.BUILD_CC:
                    if self.already_pending(
                        UnitTypeId.COMMANDCENTER
                    ) == 0 and self.can_afford(UnitTypeId.COMMANDCENTER):
                        await self.expand_now()
                case Actions.BUILD_BARRACKS:
                    if self.can_afford(UnitTypeId.BARRACKS):
                        # TODO wall main ramp
                        await self.build(
                            UnitTypeId.BARRACKS, near=random.choice(self.townhalls)
                        )
                case Actions.BUILD_GHOST_ACADEMY:
                    if self.can_afford(UnitTypeId.GHOSTACADEMY):
                        await self.build(
                            UnitTypeId.GHOSTACADEMY, near=random.choice(self.townhalls)
                        )
                case Actions.BUILD_FACTORY:
                    if self.can_afford(UnitTypeId.FACTORY):
                        await self.build(
                            UnitTypeId.FACTORY, near=random.choice(self.townhalls)
                        )
                case Actions.BUILD_STARPORT:
                    if self.can_afford(UnitTypeId.STARPORT):
                        await self.build(
                            UnitTypeId.STARPORT, near=random.choice(self.townhalls)
                        )
                case Actions.BUILD_EBAY:
                    if self.can_afford(UnitTypeId.ENGINEERINGBAY):
                        await self.build(
                            UnitTypeId.ENGINEERINGBAY,
                            near=random.choice(self.townhalls),
                        )
                case Actions.BUILD_ARMORY:
                    if self.can_afford(UnitTypeId.ARMORY):
                        await self.build(
                            UnitTypeId.ARMORY, near=random.choice(self.townhalls)
                        )
                case Actions.BUILD_FUSION_CORE:
                    if self.can_afford(UnitTypeId.FUSIONCORE):
                        await self.build(
                            UnitTypeId.FUSIONCORE, near=random.choice(self.townhalls)
                        )
                case Actions.BUILD_BUNKER:
                    if self.can_afford(UnitTypeId.BUNKER):
                        await self.build(
                            UnitTypeId.BUNKER, near=random.choice(self.townhalls)
                        )
                case Actions.BUILD_TURRET:
                    if self.can_afford(UnitTypeId.MISSILETURRET):
                        await self.build(
                            UnitTypeId.MISSILETURRET, near=random.choice(self.townhalls)
                        )
                case Actions.BUILD_SENSOR:
                    if self.can_afford(UnitTypeId.SENSORTOWER):
                        await self.build(
                            UnitTypeId.SENSORTOWER, near=random.choice(self.townhalls)
                        )
                case Actions.BUILD_ORBITAL:
                    cc = random.choice(self.townhalls)
                    if cc.is_idle and self.can_afford(UnitTypeId.ORBITALCOMMAND):
                        await cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND)
                case Actions.BUILD_PF:
                    cc = random.choice(self.townhalls)
                    if cc.is_idle and self.can_afford(UnitTypeId.PLANETARYFORTRESS):
                        await cc(AbilityId.UPGRADETOPLANETARYFORTRESS_PLANETARYFORTRESS)

                # Train Units
                case Actions.TRAIN_SCV:
                    for cc in self.townhalls:
                        worker_count = len(self.workers.closer_than(10, cc))
                        if worker_count < 22:
                            if cc.is_idle and self.can_afford(UnitTypeId.SCV):
                                cc.train(UnitTypeId.SCV)
                case Actions.TRAIN_MARINE:
                    for b in self.structures(UnitTypeId.BARRACKS).ready.idle:
                        if self.can_afford(UnitTypeId.MARINE):
                            b.train(UnitTypeId.MARINE)

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
                    for m in self.units(UnitTypeId.MARINE).idle:
                        # if we can attack:
                        if self.enemy_units.closer_than(10, m):
                            m.attack(
                                random.choice(
                                    self.all_enemy_units.closest_to(m.position)
                                )
                            )
                        elif self.enemy_start_locations:
                            # attack!
                            m.attack(self.enemy_start_locations[0])

                # case _:
        except Exception as e:
            reward -= 0.1
            print(e)

        map = np.zeros(
            (self.game_info.map_size[0], self.game_info.map_size[1], 3), dtype=np.uint8
        )

        # draw the minerals:
        for mineral in self.mineral_field:
            pos = mineral.position
            c = [175, 255, 255]
            fraction = mineral.mineral_contents / 1800
            if mineral.is_visible:
                map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction * i) for i in c]
            else:
                map[math.ceil(pos.y)][math.ceil(pos.x)] = [20, 75, 50]

        # draw the enemy start location:
        for enemy_start_location in self.enemy_start_locations:
            pos = enemy_start_location
            c = [0, 0, 255]
            map[math.ceil(pos.y)][math.ceil(pos.x)] = c

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
            map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction * i) for i in c]

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
            map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction * i) for i in c]

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
                map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction * i) for i in c]

            else:
                pos = our_structure.position
                c = [0, 255, 175]
                # get structure health fraction:
                fraction = (
                    our_structure.health / our_structure.health_max
                    if our_structure.health_max > 0
                    else 0.0001
                )
                map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction * i) for i in c]

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
                map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction * i) for i in c]
            else:
                map[math.ceil(pos.y)][math.ceil(pos.x)] = [50, 20, 75]

        # draw our units:
        for our_unit in self.units:
            # if it is a voidray:
            if our_unit.type_id == UnitTypeId.VOIDRAY:
                pos = our_unit.position
                c = [255, 75, 75]
                # get health:
                fraction = (
                    our_unit.health / our_unit.health_max
                    if our_unit.health_max > 0
                    else 0.0001
                )
                map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction * i) for i in c]

            else:
                pos = our_unit.position
                c = [175, 255, 0]
                # get health:
                fraction = (
                    our_unit.health / our_unit.health_max
                    if our_unit.health_max > 0
                    else 0.0001
                )
                map[math.ceil(pos.y)][math.ceil(pos.x)] = [int(fraction * i) for i in c]

        # show map with opencv, resized to be larger:
        # horizontal flip:
        cv2.imshow(
            "map",
            cv2.flip(
                cv2.resize(map, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST), 0
            ),
        )
        cv2.waitKey(1)

        if SAVE_REPLAY:
            # save map image into "replays dir"
            cv2.imwrite(f"replays/{int(time.time())}-{iteration}.png", map)

        # Reward logic
        # Get a smaller reward down to negatives each time you build a tech building that already exists
        #   Not rax, fac, port, cc, depot
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
            "state": map,
            "reward": reward,
            "action": None,
            "done": False,
        }  # empty action waiting for the next one!

        with open("state_rwd_action.pkl", "wb") as f:
            pickle.dump(data, f)

result = run_multiple_games(
    [
        GameMatch(
            maps.get("Oceanborn513AIE"),  # the map we are playing on
            [
                Bot(
                    Race.Terran, TerranBot()
                ),  # runs our coded bot, protoss race, and we pass our bot object
                Computer(Race.Random, Difficulty.VeryHard),
            ],  # runs a pre-made computer agent
            realtime=False,  # When set to True, the agent is limited in how long each step can take to process.
        )
    ]
)


if str(result) == "Result.Victory":
    rwd = 500
else:
    rwd = -500

with open("results.txt", "a") as f:
    f.write(f"{result}\n")


# TODO: Need to change to be map dimensions
map = np.zeros((200, 192, 3), dtype=np.uint8)
observation = map
data = {
    "state": map,
    "reward": rwd,
    "action": None,
    "done": True,
}  # empty action waiting for the next one!
with open("state_rwd_action.pkl", "wb") as f:
    pickle.dump(data, f)

cv2.destroyAllWindows()
cv2.waitKey(1)
time.sleep(3)
sys.exit()
