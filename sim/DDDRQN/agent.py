# Inspired from https://github.com/raillab/dqn
import random

from gymnasium import spaces
import numpy as np

from .model_mlp import DRQN
from .replay_buffer import ReplayBuffer
from .config import batch_size,seq_len
import torch
import torch.nn.functional as F


class DRQNAgent:
    def __init__(self,
                 observation_space,
                 action_space,
                 replay_buffer: ReplayBuffer,
                 use_double_dqn,
                 lr,
                 batch_size,
                 gamma,
                 device=torch.device("cpu" ),
                 dqn_type="neurips"):
        """
        Initialise the DQN algorithm using the Adam optimiser
        :param action_space: the action space of the environment
        :param observation_space: the state space of the environment
        :param replay_buffer: storage for experience replay
        :param lr: the learning rate for Adam
        :param batch_size: the batch size
        :param gamma: the discount factor
        """

        self.memory = replay_buffer
        self.batch_size = batch_size
        self.use_double_dqn = use_double_dqn
        self.gamma = gamma

        if(dqn_type=="neurips"):
            network = DRQN
        else:
            network = DRQN

        self.policy_network =  network(observation_space, action_space).to(device)
        self.target_network =  network(observation_space, action_space).to(device)
        self.update_target_network()
        self.target_network.eval()


        #优化器的选取
        # self.optimiser = torch.optim.RMSprop(self.policy_network.parameters() , lr=lr)
        self.optimiser = torch.optim.Adam(self.policy_network.parameters(), lr=lr)
        # self.optimizer =  torch.optim.Adadelta(self.policy_network.parameters(), lr=lr, rho=0.9)

        self.device = device

    def optimise_td_loss(self):
        """
        Optimise the TD-error over a single minibatch of transitions
        :return: the loss
        """
        device = self.device
        states, actions, rewards, next_states, dones = self.memory.batchsize_sample(self.batch_size)


        states = torch.from_numpy(states).float().to(device)
        actions = torch.from_numpy(actions).long().to(device)
        rewards = torch.from_numpy(rewards).float().to(device)
        next_states = torch.from_numpy(next_states).float().to(device)
        dones = torch.from_numpy(dones).float().to(device)

        # print("state_shape",states.shape)   torch.Size([32, 10, 13])


        h, c = self.policy_network.init_hidden_state(batch_size=batch_size, training=True)
        h_target, c_target =self.target_network.init_hidden_state(batch_size=batch_size, training=True)
        h, c, h_target, c_target = h.to(device), c.to(device), h_target.to(device), c_target.to(device)

        with torch.no_grad():
            if self.use_double_dqn:
                # _, max_next_action = self.policy_network(next_states,h,c).max(1)
                # q_values,_,_= self.policy_network(next_states, h, c) #torch.Size([batch_size, seq_len, a_space])
                # _, max_next_action = q_values.max(2)
                # print(q_values,max_next_action)
                # print( "max_next_action",max_next_action,max_next_action.shape) torch.Size([batch_size, seq_len])
                # print("max_next_action1111", self.target_network(next_states,h_target,c_target)[0].shape, max_next_action.unsqueeze(2).shape)
                # print(self.target_network(next_states,h_target,c_target)[0],self.target_network(next_states,h_target,c_target)[0].shape)
                # max_next_q_values = self.target_network(next_states,h_target,c_target)[0].gather(2, max_next_action.unsqueeze(2)).squeeze(2) #torch.Size([32,2，1])---torch.Size([32, 2])
                # print("ss",max_next_q_values.shape)

                #获取最大的动作
                V,A,_,_=self.policy_network(next_states, h, c)
                q = V + A - torch.mean(A, dim=-1, keepdim=True)#torch.Size([32, 8,24])
                _, max_next_action = q.max(2)#获取动作的最大值

                #计算q值
                V_, A_, _, _ = self.target_network(next_states, h_target, c_target)
                q_ = V_ + A_ - torch.mean(A_, dim=-1, keepdim=True)
                # torch.Size([32,2，1])---torch.Size([32, 2])
                max_next_q_values=q_.gather(2,max_next_action.unsqueeze(2)).squeeze(2)
                # print("ss",max_next_q_values.shape)

            else:
                # next_q_values,_,_ = self.target_network(next_states,h_target,c_target)
                # max_next_q_values, _ = next_q_values.max(2)

                V_, A_, _, _ = self.target_network(next_states,h_target,c_target)
                q_ = V_ + A_ - torch.mean(A_, dim=-1, keepdim=True)
                max_next_q_values, _ = q_.max(2)

            target_q_values = rewards + (1 - dones) * self.gamma * max_next_q_values #torch.Size([32,2])
            # print("ssss",target_q_values.shape)


        input_V_values,input_A_values,_,_ = self.policy_network(states,h,c)  #torch.Size([32, 2, 6])
        input_Q_values=input_V_values+input_A_values-torch.mean(input_A_values, dim=-1, keepdim=True)
        input_q_values = input_Q_values.gather(2, actions.unsqueeze(2)).squeeze(2)   #torch.Size([32,2])


        loss = F.smooth_l1_loss(input_q_values, target_q_values)
        self.optimiser.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_network.parameters(), 10)
        self.optimiser.step()
        del states
        del next_states
        return loss.item()

    def update_target_network(self):
        """
        Update the target Q-network by copying the weights from the current Q-network
        """
        self.target_network.load_state_dict(self.policy_network.state_dict())

    def act(self, state: np.ndarray, epsilon,h,c):
        """
        Select an action greedily from the Q-network given the state
        :param state: the current state
        :return: the action to take
        """
        device = self.device
        # print("state",state)

        state = torch.tensor(state, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        # print(state.shape) torch.Size([1, 1, 13])

        with torch.no_grad():
            output = self.policy_network(state.to(device), h.to(device), c.to(device))
            # print("acton", output[0].argmax().item())
            # print(output)
            # print(output[0].max(2)[1].item())


            #return V,A, new_h, new_c

            if random.random() < epsilon:
                return random.randint(0, self.policy_network.action_space-1), output[2], output[3]
            else:
                return output[1].argmax().item(), output[2], output[3]


