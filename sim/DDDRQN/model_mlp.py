import torch
from gymnasium import spaces
import torch.nn as nn
from .config import batch_size, seq_len
import torch.nn.functional as F


# Class structure loosely inspired by https://towardsdatascience.com/beating-video-games-with-deep-q-networks-7f73320b9592
class DRQN(nn.Module):
    """
    A basic implementation of a Deep Q-Network. The architecture is the same as that described in the
    Nature DQN paper.
    """

    def __init__(self,
                 observation_space,
                 action_space: spaces.Discrete):
        """
        Initialise the DQN
        :param observation_space: the state space of the environment
        :param action_space: the action space of the environment
        """
        super().__init__()
        self.hidden_space = 256
        self.action_space = action_space.n
        # self.observation_space = sum(space.shape[0] for space in observation_space.values())
        self.observation_space = 13

        self.Linear1 = nn.Linear(self.observation_space, self.hidden_space)
        # 换成了LSTM
        self.lstm = nn.LSTM(256, self.hidden_space, batch_first=True)

        self.Linear2 = nn.Linear(self.hidden_space, self.action_space)

        self.V = nn.Linear(self.hidden_space, 1)
        self.A = nn.Linear(self.hidden_space, self.action_space)



    def forward(self, x, h, c):
        x = F.relu(self.Linear1(x))
        x, (new_h, new_c) = self.lstm(x, (h, c))
        V = self.V(x)
        A = self.A(x)
        # x = self.Linear2(x)
        return V,A, new_h, new_c
    # 初始化  隐藏状态和细胞状态
    def init_hidden_state(self, batch_size, training=None):
        assert training is not None, "training step parameter should be dtermined"
        if training is True:
            return torch.zeros([1, batch_size, self.hidden_space]), torch.zeros([1, batch_size, self.hidden_space])
        else:
            return torch.zeros([1, 1, self.hidden_space]), torch.zeros([1, 1, self.hidden_space])
