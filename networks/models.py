from networks.ft_extractor import CNN_MNIST, CNN_MNIST_2, StateToFeatures
from networks.messages import MessageReceiver, MessageSender
from networks.recurrents import BeliefUnit, ActionUnit
from networks.policy import Policy
from networks.prediction import Prediction
import torch.nn as nn


class ModelsUnion:
    def __init__(self, n: int, f: int, n_m: int, d: int, nb_action: int, nb_class: int, pretrained_seq_conv_cnn: nn.Sequential=None):
        self.__b_theta_5 = CNN_MNIST(f, n)

        if pretrained_seq_conv_cnn is not None:
            self.__b_theta_5.seq_conv = pretrained_seq_conv_cnn

        #self.__b_theta_5 = CNN_MNIST_2(f, n)
        self.__d_theta_6 = MessageReceiver(n_m, n)
        self.__lambda_theta_7 = StateToFeatures(d, n)
        self.__belief_unit = BeliefUnit(n)
        self.__m_theta_4 = MessageSender(n, n_m)
        self.__action_unit = ActionUnit(n)
        self.__pi_theta_3 = Policy(nb_action, n)
        self.__q_theta_8 = Prediction(n, nb_class)

    def map_obs(self, o_t):
        return self.__b_theta_5(o_t)

    def decode_msg(self, m_t):
        return self.__d_theta_6(m_t)

    def map_pos(self, p_t):
        return self.__lambda_theta_7(p_t)

    def belief_unit(self, h_t, c_t, u_t):
        return self.__belief_unit(h_t, c_t, u_t)

    def evaluate_msg(self, h_t_next):
        return self.__m_theta_4(h_t_next.squeeze(0))

    def action_unit(self, h_caret_t, c_caret_t, u_t):
        return self.__action_unit(h_caret_t, c_caret_t, u_t)

    def policy(self, h_caret_t_next):
        return self.__pi_theta_3(h_caret_t_next.squeeze(0))

    def predict(self, c_t):
        return self.__q_theta_8(c_t.squeeze(0))

    def get_networks(self):
        return [self.__b_theta_5, self.__d_theta_6, self.__lambda_theta_7, self.__belief_unit,
                self.__m_theta_4, self.__action_unit, self.__pi_theta_3, self.__q_theta_8]

    def cuda(self):
        for n in self.get_networks():
            n.cuda()
