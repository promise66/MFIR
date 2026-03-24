import os
import csv
import torch
import numpy as np
import time
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.results_plotter import load_results, ts2xy, plot_results
import gymnasium as gym
from gymnasium import spaces
import random
from DDDRQN.agent import DRQNAgent
from DDDRQN.replay_buffer import ReplayBuffer
import argparse
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3 import DQN, PPO
from stable_baselines3.common.evaluation import evaluate_policy
from cross_layer_sim import cross_layer_Sim
class cross_layerGym(gym.Env):
    """Custom Environment that follows gym interface"""
    metadata = {"render.modes": ["human"]}

    def __init__(self, render_mode=None):
        super(cross_layerGym, self).__init__()
        random.seed(time.time())
        self.action_space = spaces.Discrete(47)
        self.observation_space = spaces.MultiDiscrete([6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7])
        self.cross_layerSim = cross_layer_Sim(48, env_name='TEModel')
        self.cost = 0
        self.ep = 0
        self.deviation = 0
        self.step_count = 0
        self.reward = 0
        # 记录最大偏移值
        self.max_deviation = 0
        self.node_compromised = 0
        self.atk_stage = 0
        self.render_mode = render_mode
        assert render_mode is None or render_mode in self.metadata["render_modes"]

    def step(self, action):
        reward, cost, property_loss, deviation, atk_stage, node_compromised, _ = self.cross_layerSim.step(action)
        self.cost += cost
        self.step_count += 1
        self.reward += reward
        done = self.cross_layerSim.isDone()
        observation = self._get_obs()
        self.deviation += deviation
        self.node_compromised += node_compromised
        info = {"cost": cost, "property_loss": property_loss, "deviation": deviation}
        if deviation > self.max_deviation:
            self.max_deviation = deviation
        if atk_stage > self.atk_stage:
            self.atk_stage = atk_stage
        if done == 0:
            done = False
        else:
            if done == 1:
                self.reward -= property_loss
            else:
                pass
            self.write_csv()
            done = True
        return observation, reward, done, info

    def write_csv(self):
        print("cost:", self.cost)
        print("ep:", self.ep)
        print("reward:", self.reward)
        print("max_deviation:", self.max_deviation)
        print("deviation:", self.deviation)
        print("node_compromised:", self.node_compromised)
        print("step_count", self.step_count)
        print("deviation_per_step:", self.deviation / self.step_count)
        print("average_cost_per_step:", self.cost / self.step_count)
        print("average_node_compromised_per_hour:", self.node_compromised / self.step_count * 5)
        print("atk_stage", self.atk_stage)
        print('=======================')

        data = {
            "cost": self.cost,
            "ep": self.ep,
            "reward": self.reward,
            "max_deviation": self.max_deviation,
            "deviation": self.deviation,
            "node_compromised": self.node_compromised,
            "step_count": self.step_count,
            "deviation_per_step": self.deviation / self.step_count,
            "average_cost_per_step": self.cost / self.step_count,
            "atk_stage": self.atk_stage,
            "average_node_compromised_per_hour": self.node_compromised / self.step_count * 5

        }

        with open('output.csv', 'a', newline='') as csvfile:
            fieldnames = ["cost", "ep", "reward", "max_deviation", "deviation", "node_compromised", "step_count",
                          "deviation_per_step", "average_cost_per_step","atk_stage", "average_node_compromised_per_hour"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if csvfile.tell() == 0:
                writer.writeheader()
            writer.writerow(data)

    def _get_obs(self):
        return self.cross_layerSim.get_obs()

    def reset(self, seed=None, options=None):
        self.deviation = 0
        self.cost = 0
        self.ep += 1
        self.reward = 0
        self.step_count = 0
        self.max_deviation = 0
        self.node_compromised = 0
        self.atk_stage = 0
        random.seed(time.time())
        self.cross_layerSim.reset()
        observation = self._get_obs()
        return observation

    def render(self, mode="human"):
        self.cross_layerSim.show()

    def close(self):
        pass


class SaveOnBestTrainingRewardCallback(BaseCallback):
    """
    Callback for saving a model (the check is done every ``check_freq`` steps)
    based on the training reward (in practice, we recommend using ``EvalCallback``).

    :param check_freq:
    :param log_dir: Path to the folder where the model will be saved.
      It must contains the file created by the ``Monitor`` wrapper.
    :param verbose: Verbosity level.
    """

    def __init__(self, check_freq: int, log_dir: str, verbose: int = 1):
        super(SaveOnBestTrainingRewardCallback, self).__init__(verbose)
        self.check_freq = check_freq
        self.log_dir = log_dir
        self.save_path = os.path.join(log_dir, 'cross_layer_24w_contrast_best_PP0_42')
        self.best_mean_reward = -np.inf

    def _init_callback(self) -> None:
        # Create folder if needed
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:

            # Retrieve training reward
            x, y = ts2xy(load_results(self.log_dir), 'timesteps')
            if len(x) > 0:
                # Mean training reward over the last 100 episodes
                mean_reward = np.mean(y[-100:])
                if self.verbose > 0:
                    print(f"Num timesteps: {self.num_timesteps}")
                    print(
                        f"Best mean reward: {self.best_mean_reward:.2f} - Last mean reward per episode: {mean_reward:.2f}")

                # New best model, you could save the agent here
                if mean_reward > self.best_mean_reward:
                    self.best_mean_reward = mean_reward
                    # Example for saving best model
                    if self.verbose > 0:
                        print(f"Saving new best model to {self.save_path}")
                    self.model.save(self.save_path)

        return True


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='DRQN Atari')
    parser.add_argument('--load-checkpoint-file', type=str, default=None,
                        help='Where checkpoint file should be loaded from (usually results/checkpoint.pth)')

    args = parser.parse_args()
    # If you have a checkpoint file, spend less time exploring
    if (args.load_checkpoint_file):
        eps_start = 0.01
    else:
        eps_start = 1

    hyper_params = {
        "seed": 42,  # which seed to use
        "replay-buffer-size": int(20000),  # replay buffer size
        "learning-rate": 1e-3,  # learning rate for Adam optimizer
        "discount-factor": 0.99,  # discount factor
        "dqn_type": "neurips",
        # total number of steps to run the environment for
        "num-steps": int(1e6),
        "batch-size": 32,  # number of transitions to optimize at the same time
        "learning-starts": 1000,  # number of steps before learning starts
        "learning-freq": 1,  # number of iterations between every optimization step
        "use-double-dqn": True,  # use double deep Q-learning
        "target-update-freq": 200,  # number of iterations between every target network update
        "eps-start": eps_start,  # e-greedy start threshold
        "eps-end": 0.01,  # e-greedy end threshold
        "eps-fraction": 0.1,  # fraction of num-steps
        "print-freq": 10,
        "eposide": 3
    }

    np.random.seed(hyper_params["seed"])
    random.seed(hyper_params["seed"])

    # assert "NoFrameskip" in hyper_params["env"], "Require environment with no frameskip"
    env = cross_layerGym()

    replay_buffer = ReplayBuffer(hyper_params["replay-buffer-size"])

    agent = DRQNAgent(
        env.observation_space,
        env.action_space,
        replay_buffer,
        use_double_dqn=hyper_params["use-double-dqn"],
        lr=hyper_params['learning-rate'],
        batch_size=hyper_params['batch-size'],
        gamma=hyper_params['discount-factor'],
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
        dqn_type=hyper_params["dqn_type"]
    )

    if (args.load_checkpoint_file):
        print(f"Loading a policy - {args.load_checkpoint_file} ")
        agent.policy_network.load_state_dict(
            torch.load(args.load_checkpoint_file))

    eps_timesteps = hyper_params["eps-fraction"] * \
                    float(hyper_params["num-steps"])

    episode_rewards = []
    t = 0
    best_reward=-200


    for i in range(hyper_params["eposide"]):
        state = env.reset()
        # print("init_state",state)
        done = False

        episode_rewards.append(0.0)
        h, c = agent.policy_network.init_hidden_state(batch_size=hyper_params['batch-size'], training=False)

        while not done:
            fraction = min(1.0, float(t) / eps_timesteps)
            eps_threshold = hyper_params["eps-start"] + fraction * \
                            (hyper_params["eps-end"] - hyper_params["eps-start"])
            action, h, c = agent.act(state, eps_threshold, h, c)
            next_state, reward, done, info = env.step(action)
            if i>=900  and i<=950 and i%5==0 :
                with open('result/Analyis/record.csv', 'a', newline='') as csvfile:
                    fieldnames = ['EP','STATE', 'ACTION','NEXT_STATE']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    if csvfile.tell() == 0:
                        writer.writeheader()
                    writer.writerow({'EP':i,'STATE': state, 'ACTION': action, 'NEXT_STATE': next_state})
            agent.memory.add(state, action, reward, next_state, float(done))
            state = next_state
            episode_rewards[-1] += reward
            t += 1
            if t > hyper_params["learning-starts"] and t % hyper_params["learning-freq"] == 0:
                agent.optimise_td_loss()

            if t > hyper_params["learning-starts"] and t % hyper_params["target-update-freq"] == 0:
                agent.update_target_network()

            num_episodes = len(episode_rewards)

            if done and hyper_params["print-freq"] is not None and len(episode_rewards) % hyper_params[
                "print-freq"] == 0:
                if episode_rewards[-1]>best_reward:
                    best_reward=episode_rewards[-1]
                    torch.save(agent.policy_network.state_dict(), f'DRQN_checkpoint.pth')
                mean_100ep_reward = round(np.mean(episode_rewards[-101:-1]), 1)
                print("********************************************************")
                print("steps: {}".format(t))
                print("episodes: {}".format(num_episodes))
                print("mean 100 episode reward: {}".format(mean_100ep_reward))
                print("% time spent exploring: {}".format(int(100 * eps_threshold)))
                print('best_reward:',best_reward)
                print("********************************************************")
                np.savetxt('Rewards_per_episode.csv', episode_rewards,
                           delimiter=',', fmt='%1.3f')
