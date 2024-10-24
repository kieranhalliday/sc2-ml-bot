import os
import time

import wandb
from stable_baselines3 import PPO
from wandb.integration.sb3 import WandbCallback

from sc2env import Sc2Env

TRAINING = True

env = Sc2Env()

# Play a game with a given model
# To play with a different model, update the model name and which zip to use
model_name = 1727844205
LOAD_MODEL = f"data/models/{model_name}/90000.zip"

# load or create the model:
model = None
if os.path.exists(LOAD_MODEL):
    model = PPO.load(LOAD_MODEL, env=env)
    print(f"Loading model {LOAD_MODEL}")
else:
    model_name = f"{int(time.time())}"
    print(f"Creating model {model_name}")

    # View logs: tensorboard --logdir=data/logs
    models_dir = f"data/models/{model_name}/"
    logdir = f"data/logs/{model_name}/"

    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

    if not os.path.exists(logdir):
        os.makedirs(logdir)

    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=logdir)


conf_dict = {
    "Model": "v19",
    "Machine": "Main",
    "policy": "MlpPolicy",
    "model_save_name": model_name,
    "load_model": LOAD_MODEL,
}

run = wandb.init(
    project=f"sc2-ml-bot",
    entity="halliminga",
    dir="data/",
    config=conf_dict,
    sync_tensorboard=True,  # auto-upload sb3's tensorboard metrics
    save_code=True,  # save source code
)

if not TRAINING:
    obs, _seed = env.reset()
    done = False


if TRAINING:
    TIMESTEPS = 10000
    iters = 0
    while True:
        print("On iteration: ", iters)
        iters += 1
        model.learn(
            total_timesteps=TIMESTEPS, reset_num_timesteps=False, tb_log_name=f"PPO"
        )
        model.save(f"{models_dir}/{TIMESTEPS*iters}")
else:
    while not done:
        action, _states = model.predict(obs)
        obs, rewards, done, truncated, info = env.step(action)
