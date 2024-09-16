import gymnasium
from gymnasium import spaces
import numpy as np
import subprocess
import pickle
import time
import os
from actions import bot_actions

import constants


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

        # waits for the new state to return (map and reward) (no new action yet. )
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
                map = np.zeros(
                    (constants.MAX_MAP_HEIGHT, constants.MAX_MAP_WIDTH, 3),
                    dtype=np.uint8,
                )
                observation = map
                # if still failing, input an ACTION, 98 (scout)
                data = {
                    "state": map,
                    "reward": 0,
                    "action": 98,
                    "done": False,
                }  # empty action waiting for the next one!
                with open("data/state_rwd_action.pkl", "wb") as f:
                    pickle.dump(data, f)

                state = map
                reward = 0
                done = False
                action = 98

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
        map = np.zeros(
            (constants.MAX_MAP_HEIGHT, constants.MAX_MAP_WIDTH, 3), dtype=np.uint8
        )
        observation = map
        data = {
            "state": map,
            "reward": 0,
            "action": None,
            "done": False,
        }  # empty action waiting for the next one!
        with open("data/state_rwd_action.pkl", "wb") as f:
            pickle.dump(data, f)

        # run bot.py non-blocking:
        subprocess.Popen(["python3", "bot.py"])
        return observation, None  # reward, done, info can't be included
