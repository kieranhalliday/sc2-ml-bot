from stable_baselines3 import PPO
import os
from sc2env import Sc2Env
import time
from wandb.integration.sb3 import WandbCallback
import wandb

# Continue training an existing model
LOAD_MODEL = "data/models/1726325503/1000.zip"
# Environment:
env = Sc2Env()

# load the model:
model = PPO.load(LOAD_MODEL, env=env)

model_name = f"{int(time.time())}"

models_dir = f"data/models/{model_name}/"
# View logs: tensorboard --logdir=data/logs
logdir = f"data/logs/{model_name}/"


conf_dict = {
    "Model": "load-v16s",
    "Machine": "Puget/Desktop/v18/2",
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


# further train:
TIMESTEPS = 10000
iters = 0
while True:
    print("On iteration: ", iters)
    iters += 1
    model.learn(
        total_timesteps=TIMESTEPS, reset_num_timesteps=False, tb_log_name=f"PPO"
    )
    model.save(f"{models_dir}/{TIMESTEPS*iters}")
