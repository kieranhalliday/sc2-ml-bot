from stable_baselines3 import PPO
from sc2env import Sc2Env

# Play a game with a given model
LOAD_MODEL = "data/models/1726325503/1000.zip"
# Environment:
env = Sc2Env()

# load the model:
model = PPO.load(LOAD_MODEL)

# Play the game:
obs, _seed = env.reset()
done = False
while not done:
    action, _states = model.predict(obs)
    obs, rewards, done, truncated, info = env.step(action)
