import os
import time

import wandb
from stable_baselines3 import PPO
from wandb.integration.sb3 import WandbCallback

from sc2env import Sc2Env

# Create a new model to train
model_name = f"{int(time.time())}"

models_dir = f"data/models/{model_name}/"
# View logs: tensorboard --logdir=data/logs
logdir = f"data/logs/{model_name}/"


conf_dict = {
    "Model": "v19",
    "Machine": "Main",
    "policy": "MlpPolicy",
    "model_save_name": model_name,
}


run = wandb.init(
    project=f"sc2-ml-bot",
    config=conf_dict,
    dir="data/",
    sync_tensorboard=True,  # auto-upload sb3's tensorboard metrics
    save_code=True,  # optional
)


if not os.path.exists(models_dir):
    os.makedirs(models_dir)

if not os.path.exists(logdir):
    os.makedirs(logdir)

env = Sc2Env(training=True)

model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=logdir)

TIMESTEPS = 10000
iters = 0
while True:
    print("On iteration: ", iters)
    iters += 1
    model.learn(
        total_timesteps=TIMESTEPS, reset_num_timesteps=False, tb_log_name=f"PPO"
    )
    model.save(f"{models_dir}/{TIMESTEPS*iters}")
