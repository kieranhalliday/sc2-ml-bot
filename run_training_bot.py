import math
import pickle
import random
import sys
import time

import cv2
import numpy as np
from sc2 import maps  # maps method for loading maps to play in.
from sc2.data import Difficulty, Race  # difficulty for bots, race for the 1 of 3 races
from sc2.main import (  # function that facilitates actually running the agents in games
    GameMatch,
    run_multiple_games,
)
from sc2.player import (  # wrapper for whether or not the agent is one of your bots, or a "computer" player
    Bot,
    Computer,
)

from src import constants
from src.bots.training_bot import TrainingBot

result = run_multiple_games(
    [
        GameMatch(
            maps.get("SiteDelta513AIE"),  # the map we are playing on
            [
                Bot(
                    Race.Terran, TrainingBot()
                ),  # runs our coded bot, protoss race, and we pass our bot object
                Computer(Race.Random, Difficulty.Hard),
            ],  # runs a pre-made computer agent
            realtime=False,  # When set to True, the agent is limited in how long each step can take to process.
        )
    ]
)


if str(result) == "Result.Victory":
    rwd = 500
else:
    rwd = -500

with open("data/results.txt", "a") as f:
    f.write(f"{result}\n")


observation = np.zeros(
    (constants.MAX_MAP_HEIGHT, constants.MAX_MAP_WIDTH, 3), dtype=np.uint8
)
data = {
    "state": observation,
    "reward": rwd,
    "action": None,
    "done": True,
}  # empty action waiting for the next one!
with open("data/state_rwd_action.pkl", "wb") as f:
    pickle.dump(data, f)

cv2.destroyAllWindows()
cv2.waitKey(1)
time.sleep(3)
sys.exit()
