import numpy as np
from sc2.bot_ai import Race
from sc2.data import Race  # difficulty for bots, race for the 1 of 3 races
from sc2.data import Result

from src.bots.action_handler_bot import ActionHandlerBotMixin
from src.bots.micro_bot import MicroBotMixin
from src.bots.reactive_bot import ReactiveBotMixin

total_steps = 10000
steps_for_pun = np.linspace(0, 1, total_steps)
step_punishment = ((np.exp(steps_for_pun**3) / 10) - 0.1) * 10


class TrainingBot(MicroBotMixin, ActionHandlerBotMixin, ReactiveBotMixin):
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

    async def on_step(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
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
