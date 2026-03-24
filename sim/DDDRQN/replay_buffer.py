import random

import cv2
import numpy as np
from .config import *


class ReplayBuffer:
    """
    Simple storage for transitions from an environment.
    """

    def __init__(self, size):
        """
        Initialise a buffer of a given size for storing transitions
        :param size: the maximum number of transitions that can be stored
        """
        self._storage = []
        self._maxsize = size
        self._next_idx = 0

    def __len__(self):
        return len(self._storage)

    def add(self, state, action, reward, next_state, done):
        """
        Add a transition to the buffer. Old transitions will be overwritten if the buffer is full.
        :param state: the agent's initial state
        :param action: the action taken by the agent
        :param reward: the reward the agent received
        :param next_state: the subsequent state
        :param done: whether the episode terminated
        """
        data = (state, action, reward, next_state, done)

        if self._next_idx >= len(self._storage):
            self._storage.append(data)
        else:
            self._storage[self._next_idx] = data
        self._next_idx = (self._next_idx + 1) % self._maxsize


    # def _encode_sample(self, indices):
    #     states, actions, rewards, next_states, dones = [], [], [], [], []
    #     for i in indices:
    #         data = self._storage[i]
    #         state, action, reward, next_state, done = data
    #         states.append(np.array(state, copy=False))
    #         actions.append(action)
    #         rewards.append(reward)
    #         next_states.append(np.array(next_state, copy=False))
    #         dones.append(done)
    #     return np.array(states), np.array(actions), np.array(rewards), np.array(next_states), np.array(dones)

    def batchsize_sample(self, batch_size):
        """
        Randomly sample a batch of transitions from the buffer.
        :param batch_size: the number of transitions to sample
        :return: a mini-batch of sampled transitions
        """
        # indices = np.random.randint(0, len(self._storage) - 1, size=batch_size)

        s_batch1, a_batch1, r_batch1, sn_batch1, t_batch1 = [], [], [], [], []

        # print('=======',self._storage.__len__())

        for k in range(batch_size):  # 每个有32个数据，其中每个数据长度为11
            s_batch, a_batch, r_batch, sn_batch, t_batch = self.sample(seq_len)  # 一次去11个数据
            # print(np.array(s_batch).shape)
            s_batch1.append(s_batch)
            a_batch1.append(a_batch)
            r_batch1.append(r_batch)
            sn_batch1.append(sn_batch)
            t_batch1.append(t_batch)

        # print(np.array(s_batch1).shape)
        # print(np.array(a_batch1).shape)
        # print(np.array(r_batch1).shape)
        # print(np.array(sn_batch1).shape)
        # print(np.array(t_batch1).shape)

        return  np.array(s_batch1),np.array(a_batch1),np.array(r_batch1),np.array(sn_batch1),np.array(t_batch1)


        # return self._encode_sample(mini_batch)

    def sample(self, seq_len):
        """
        Randomly sample a batch of transitions from the buffer.
        :param batch_size: the number of transitions to sample
        :return: a mini-batch of sampled transitions
        """
        # indices = np.random.randint(0, len(self._storage) - 1, size=batch_size)\
        random_idx = random.randint(0, len(self._storage) - seq_len)
        # print(random_idx)
        mini_batch = self._storage[random_idx: random_idx + seq_len]

        states, actions, rewards, next_states, dones = [], [], [], [], []
        for data in mini_batch:
            state, action, reward, next_state, done = data

            # cv2.imshow("normGray", state)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()

            states.append(np.array(state, copy=False))
            actions.append(action)
            rewards.append(reward)
            next_states.append(np.array(next_state, copy=False))
            dones.append(done)
        return states, actions, rewards, next_states, dones



        # return self._encode_sample(mini_batch)
