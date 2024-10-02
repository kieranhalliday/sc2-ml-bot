import numpy as np
from sc2.bot_ai import Race
from sc2.data import Race  # difficulty for bots, race for the 1 of 3 races
from sc2.data import Result
from stable_baselines3 import PPO

from bots.micro_bot import MicroBotMixin
from bots.reactive_bot import ReactiveBotMixin
from sc2env import Sc2Env
from src.action_handler import ActionHandler

total_steps = 10000
steps_for_pun = np.linspace(0, 1, total_steps)
step_punishment = ((np.exp(steps_for_pun**3) / 10) - 0.1) * 10

# Play a game with a given model
LOAD_MODEL = "data/models/1727755392/200.zip"

# Environment:
env = Sc2Env()

# load the model:
model = PPO.load(LOAD_MODEL, env=env)


class CompetitiveBot(MicroBotMixin, ActionHandler, ReactiveBotMixin):
    NAME: str = "Raynor's Raider"
    RACE: Race = Race.Terran

    # Play the game:
    obs = None

    async def on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        print("Game started")
        self.obs, _seed = env.reset()

    async def on_step(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        action, _states = model.predict(self.obs)
        self.obs, rewards, done, truncated, info = env.step(action)

        micro_mode = await self.handle_chosen_action(iteration)
        if micro_mode in ["attack", "defend"]:
            self.set_micro_mode(micro_mode)
        await self.on_step_micro(iteration)

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
        print(result)
