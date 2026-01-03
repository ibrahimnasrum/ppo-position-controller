import gymnasium as gym
import numpy as np
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import matplotlib.pyplot as plt
from stable_baselines3.common.callbacks import BaseCallback
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.monitor import Monitor

class DCMotorPotEnv(gym.Env):
    def __init__(self):
        super().__init__()
        self.max_position = 1023.0
        self.max_pwm = 255.0
        self.max_steps = 500

        self.actual_position = 0.0
        self.setpoint = self._generate_setpoint()
        self.step_count = 0

        # Limit action range slightly to avoid overshooting
        self.action_space = spaces.Box(low=0.0, high=0.8, shape=(1,), dtype=np.float32)

        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32)
        )

    def _generate_setpoint(self):
        return np.random.uniform(100, self.max_position)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.actual_position = np.random.uniform(0, 100)
        self.setpoint = self._generate_setpoint()
        self.step_count = 0
        return self._get_obs(), {}

    def _get_obs(self):
        return np.array([
            self.actual_position / self.max_position,
            self.setpoint / self.max_position
        ], dtype=np.float32)

    def step(self, action):
        pwm_norm = float(np.clip(action[0], 0.0, 1.0))
        pwm = pwm_norm * self.max_pwm

        # Clip delta to prevent excessive jumps
        delta = np.sign(self.setpoint - self.actual_position) * pwm * 0.03
        delta = np.clip(delta, -10.0, 10.0)
        self.actual_position += delta
        self.actual_position = np.clip(self.actual_position, 0, self.max_position)

        error = abs(self.setpoint - self.actual_position)

        # Improved reward shaping
        reward = - (error / self.max_position) ** 2
        reward -= 0.01 * pwm_norm
        if error < 2.0:
            reward += 2.0

        reward = np.clip(reward, -1.0, 2.0)

        self.step_count += 1
        done = error < 2.0 or self.step_count >= self.max_steps
        return self._get_obs(), reward, done, False, {}


class DCMotorPotEnv(gym.Env):
    def __init__(self):
        super().__init__()
        self.max_position = 1023.0
        self.max_pwm = 255.0
        self.max_steps = 500

        self.actual_position = 0.0
        self.setpoint = self._generate_setpoint()
        self.step_count = 0

        # Limit action range slightly to avoid overshooting
        self.action_space = spaces.Box(low=0.0, high=0.8, shape=(1,), dtype=np.float32)

        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32)
        )

    def _generate_setpoint(self):
        return np.random.uniform(100, self.max_position)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.actual_position = np.random.uniform(0, 100)
        self.setpoint = self._generate_setpoint()
        self.step_count = 0
        return self._get_obs(), {}

    def _get_obs(self):
        return np.array([
            self.actual_position / self.max_position,
            self.setpoint / self.max_position
        ], dtype=np.float32)

    def step(self, action):
        pwm_norm = float(np.clip(action[0], 0.0, 1.0))
        pwm = pwm_norm * self.max_pwm

        # Clip delta to prevent excessive jumps
        delta = np.sign(self.setpoint - self.actual_position) * pwm * 0.03
        delta = np.clip(delta, -10.0, 10.0)
        self.actual_position += delta
        self.actual_position = np.clip(self.actual_position, 0, self.max_position)

        error = abs(self.setpoint - self.actual_position)

        # Improved reward shaping
        reward = - (error / self.max_position) ** 2
        reward -= 0.01 * pwm_norm
        if error < 2.0:
            reward += 2.0

        reward = np.clip(reward, -1.0, 2.0)

        self.step_count += 1
        done = error < 2.0 or self.step_count >= self.max_steps
        return self._get_obs(), reward, done, False, {}


class RewardLogger:
    def __init__(self):
        self.episode_rewards = []
        self.current_rewards = []

    def __call__(self, locals_, globals_):
        reward = locals_.get("rewards", [0])[0]
        done = locals_.get("dones", [False])[0]
        self.current_rewards.append(reward)
        if done:
            self.episode_rewards.append(sum(self.current_rewards))
            self.current_rewards = []
        return True


# === Environment Wrapping ===
env = DummyVecEnv([lambda: Monitor(DCMotorPotEnv())])
env = VecNormalize(env, norm_obs=True, norm_reward=False)

# === PPO Model ===
model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    learning_rate=5e-4,
    n_steps=1024,
    batch_size=128,
    gamma=0.98,
    gae_lambda=0.95,
    ent_coef=0.0001,  
    device="cpu"
)

reward_logger = RewardLogger()
model.learn(total_timesteps=100_000, callback=reward_logger)  
model.save("ppo_dc_motor_model")

# === Plot Training Reward ===
plt.plot(reward_logger.episode_rewards, label="Episode Reward")
plt.xlabel("Episode")
plt.ylabel("Total Reward")
plt.title("Training Reward Progress")
plt.grid(True)
plt.legend()
plt.show()
