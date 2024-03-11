import time
import random
from multiprocessing import Process, Queue, Manager

# Cette classe génère des valeurs aléatoires de latence et de bande passante avec des
# pertubations toutes les 5 secondes (aleatoires).
# Ces valeurs sont placées dans une file d'attente pour être accessibles à d'autres processus


class ValeursStatistiques:
    def __init__(self, x, valeurs_queue, valeurs_list):
        self.x = x
        self.latence = 0.0
        self.bande_passante = 0.0
        self.perturbe = False
        self.valeurs_queue = valeurs_queue
        self.valeurs_en_temps_reel = valeurs_list

    def generer_valeurs(self):
        self.latence = random.uniform(5, 10)
        self.bande_passante = random.uniform(15, 20)

    def perturber_reseau(self):
        self.latence_perturbee = random.uniform(15, 20)
        self.bande_passante_perturbee = random.uniform(5, 10)
        self.perturbe = True

    def reinitialiser_reseau(self):
        self.perturbe = False

    def executer(self):
        perturbation_timer = 0
        while True:
            if not self.perturbe:
                self.generer_valeurs()
                valeurs = {
                    'latence': self.latence,
                    'bande_passante': self.bande_passante
                }
                self.valeurs_queue.put(valeurs)
                self.valeurs_en_temps_reel.append(valeurs)
            else:
                self.perturber_reseau()
                valeurs = {
                    'latence_perturbee': self.latence_perturbee,
                    'bande_passante_perturbee': self.bande_passante_perturbee
                }
                self.valeurs_queue.put(valeurs)
                self.valeurs_en_temps_reel.append(valeurs)
                perturbation_timer += self.x
                if perturbation_timer >= 5:
                    self.reinitialiser_reseau()

            time.sleep(self.x)
            if not self.perturbe and random.random() < 0.3:  # probabilité de 30% de perturbation du réseau
                self.perturber_reseau()

def afficher_valeurs_en_temps_reel(valeurs_queue):
    while True:
        if not valeurs_queue.empty():
            valeurs = valeurs_queue.get()

            # print("Valeurs reçues:")
            # for key, value in valeurs.items():
            #     print(f"{key}: {value}")
            # print()
