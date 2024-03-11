import gym
from gym import spaces
import numpy as np
from numpy.random import default_rng

############################################################################################################
# 1. La classe SDWANEnv hérite de la classe gym.Env.
# Cette classe représente l'environnement d'apprentissage
# Elle possède deux espaces : un espace d'actions et un espace d'observations.
# L'espace d'actions est défini comme discret avec deux actions possibles (INTERNET et MPLS).
# L'espace d'observations est défini comme une boîte avec des valeurs réelles allant de 0 à l'infini et
# une dimension de 3 (latence, bande passante, perte de paquets).
# remarque : la perte de paquet n'est

# 2. La méthode reset est utilisée pour réinitialiser l'environnement (les valeurs des états).
# Elle prend en entrée les valeurs initiales de la latence, de la bande passante, du nombre de flux et
# du type de flux. Eventuellement, cette méthode peut génèrer des valeurs aléatoires pour la latence, la bande passante et
# la perte de paquets pour faire des tests.


# 3. La méthode step est utilisée pour effectuer une étape dans l'environnement en fonction de l'action donnée.
# On rappele q'un épisode est un ensemble de step (ou itérations)
# Selon l'action, la latence, la bande passante et la perte de paquets sont modifiées (à modifier).
# La récompense est calculée en fonction de l'action et de l'état actuel de l'environnement.
# La méthode renvoie la nouvelle observation, la récompense, un indicateur de fin d'épisode.

# 4. La méthode get_observation renvoie l'observation actuelle de l'environnement, qui est un tableau numpy
# contenant la latence, la bande passante et la perte de paquets.

# 5. La méthode get_reward calcule la récompense en fonction de l'action et de l'état actuel de
# l'environnement. La récompense est calculée différemment en fonction du port du flux actuel.
# Si l'action est MPLS, la récompense est pénalisée. La récompense finale est multipliée par
# le nombre de flux pour tenir compte de plusieurs flux.

import gym
from gym import spaces
import numpy as np

class SDWANEnv(gym.Env):

    def __init__(self):
        self.action_space = spaces.Discrete(2)  # 2 actions : 0 (INTERNET), 1 (MPLS)
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(3,), dtype=np.float32)  # [latence, bande passante, perte de paquets]
        self.latency_min = 2
        self.bandwidth_max = 25
        self.nb_flow = None
        self.current_flows = {}

    def reset(self, latency, bandwidth, nb_flow,flow=None):
        self.latency = latency
        self.bandwidth = bandwidth
        self.packet_loss = np.random.uniform(0, 1)
        self.nb_flow = nb_flow
        self.current_flows = flow

        return self.get_observation()

    def step(self, action):
        if action == 0:  # INTERNET
            if self.latency >= 10 and self.bandwidth <= self.bandwidth_max:  # Priorité à internet si latence haute et BP faible
                self.latency -= 0.5
                self.bandwidth += 0.5
            else:
                self.latency -= 1
                self.bandwidth += 1.5
        elif action == 1:  # MPLS diminue plus rapidement la latence et augmente plus la BP
            self.latency -= 1
            self.bandwidth += 1.5

        self.latency = max(self.latency_min, self.latency)
        self.bandwidth = min(self.bandwidth_max, self.bandwidth)

        done = self.latency <= self.latency_min or self.bandwidth >= self.bandwidth_max
        reward = self.get_reward(action)

        return self.get_observation(), reward, done, {}

    def get_observation(self):
        return np.array([self.latency, self.bandwidth, self.packet_loss])

    def get_reward(self, action):
        if self.current_flows is None:
            return 0

        reward = 0
        for port in self.current_flows:
            if port == '443':
                reward = -5 * self.latency + 0.8 * self.bandwidth
            else:
                reward = -20 * self.latency + 0.2 * self.bandwidth

        if action == 1:  # Penalize if choosing MPLS
            reward = -10 * reward

        reward *= self.nb_flow

        return reward
