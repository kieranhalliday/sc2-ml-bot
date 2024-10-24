import os
import pickle
import subprocess
import time

import gymnasium
import numpy as np
from gymnasium import spaces

import src.constants as constants
from src.actions import bot_actions


class Sc2Env(gymnasium.Env):
    """Custom Environment that follows gym interface"""

    def __init__(self):
        super(Sc2Env, self).__init__()

        # Define action and observation space
        # They must be gym.spaces objects
        self.action_space = spaces.Discrete(len(bot_actions))
        self.observation_space = spaces.Box(
            low=0,
            high=255,
            shape=(constants.MAX_MAP_HEIGHT, constants.MAX_MAP_WIDTH, 3),
            dtype=np.uint8,
        )

    def step(self, action):
        wait_for_action = True
        while wait_for_action:
            try:
                with open("data/state_rwd_action.pkl", "rb") as f:
                    state_rwd_action = pickle.load(f)

                    if state_rwd_action["action"] is not None:
                        wait_for_action = True
                    else:
                        wait_for_action = False
                        state_rwd_action["action"] = action
                        with open("data/state_rwd_action.pkl", "wb") as f:
                            # now we've added the action.
                            pickle.dump(state_rwd_action, f)
            except Exception as e:
                # print(str(e))
                pass

        # waits for the new state to return (observation and reward) (no new action yet. )
        wait_for_state = True
        while wait_for_state:
            try:
                if os.path.getsize("data/state_rwd_action.pkl") > 0:
                    with open("data/state_rwd_action.pkl", "rb") as f:
                        state_rwd_action = pickle.load(f)
                        if state_rwd_action["action"] is None:
                            wait_for_state = True
                        else:
                            state = state_rwd_action["state"]
                            reward = state_rwd_action["reward"]
                            done = state_rwd_action["done"]
                            wait_for_state = False

            except Exception as e:
                wait_for_state = True
                observation = np.zeros(
                    (constants.MAX_MAP_HEIGHT, constants.MAX_MAP_WIDTH, 3),
                    dtype=np.uint8,
                )
                # if still failing, input an ACTION, scout
                data = {
                    "state": observation,
                    "reward": 0,
                    "action": bot_actions[-1],
                    "done": False,
                }  # empty action waiting for the next one!
                with open("data/state_rwd_action.pkl", "wb") as f:
                    pickle.dump(data, f)

                state = observation
                reward = 0
                done = False
                action = bot_actions[-1]

        info = {}
        truncated = {}
        observation = state
        return (
            observation,
            reward,
            done,
            truncated,
            info,
        )

    def reset(self, seed=int(time.time())):
        print("Resetting environment")
        observation = np.zeros(
            (constants.MAX_MAP_HEIGHT, constants.MAX_MAP_WIDTH, 3), dtype=np.uint8
        )
        data = {
            "state": observation,
            "reward": 0,
            "action": None,
            "done": False,
        }  # empty action waiting for the next one!
        with open("data/state_rwd_action.pkl", "wb") as f:
            pickle.dump(data, f)

        return observation, None  # reward, done, info can't be included
