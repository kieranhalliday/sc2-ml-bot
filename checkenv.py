from sc2env import Sc2Env
from stable_baselines3.common.env_checker import check_env

env = Sc2Env()
check_env(env)

# Double check env
episodes = 50
for episode in range(episodes):
	done = False
	obs = env.reset()
	while not done:
		random_action = env.action_space.sample()
		print("action",random_action)
		obs, reward, done, info = env.step(random_action)
		print('reward',reward)