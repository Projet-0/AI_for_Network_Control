from DQN import Agent
from Utils import plotLearning
import numpy as np
from SdwanEnv import SDWANEnv
from GenererStat import *

##############################################################################################################################
######################################## MAIN (SIMULATION DE l'IA)  ##############################################################
##############################################################################################################################

## On réalise ici un apprentissage continu par simulation de données

## Note :

## Dans cette version, on choisit 1 seul flux (port 443) qui priorise une bonne bande passante pour adapter les chemins
## On peut envoyer les données a une frequence de temps souhaitée : dans le cas réel, faire attention car il y peut y avoir des erreurs de mesures avec les protocoles de sondages.
## L'influence du nombre de flux n'est pas implémenté : on peut supposer que ci-celui est elevé alors il y a plus de pertes de paquets, plus de latence, moins de bande passante
## Pour adapter la simulation à une situation réelle, il faut modifier les valeurs (rigoureusement aleatoires) de latence et bande passante lorsque le réseau est normal et quand
## il est congestionné (voir dans GenererStat.py)


##On trace le graphe de la simulation (apres fin de la simulation) dans 'Sdwan.png'


if __name__ == '__main__':

    print("Lancement de l'apprentissage")
    env = SDWANEnv()
    agent = Agent(gamma=0.99, epsilon=1.0, batch_size=64, n_actions=2, eps_end=0.01, input_dims=[3], lr=0.001)
    scores, eps_history, avg_scores = [], [], []
    n_train_episodes = 10000

    temps_collecte_données_controlleur=0.5 # en secondes

    ########## GENERATION DES STATISTIQUES en continue #############

    with Manager() as manager:
        valeurs_queue = Queue()
        valeurs_list = manager.list()
        valeurs_statistiques = ValeursStatistiques(temps_collecte_données_controlleur, valeurs_queue, valeurs_list)

        process_valeurs_statistiques = Process(target=valeurs_statistiques.executer)
        process_affichage = Process(target=afficher_valeurs_en_temps_reel, args=(valeurs_queue,))

        process_valeurs_statistiques.start()
        process_affichage.start()

        i=0
        while True:
            try:
                if valeurs_list:
                    i+=1
                    valeurs = valeurs_list.pop(0)
                    if 'latence' in valeurs or 'latence_perturbee' in valeurs:
                        if 'latence' in valeurs:
                            latency = valeurs['latence']
                            bandepassante = valeurs['bande_passante']
                            print("Valeurs normales reçues:")
                        elif 'latence_perturbee' in valeurs:
                            latency = valeurs['latence_perturbee']
                            bandepassante = valeurs['bande_passante_perturbee']
                            print("Valeurs perturbées reçues:")

                    score = 0
                    done = False

                    observation = env.reset(latency=latency, bandwidth=bandepassante, nb_flow=1,
                                            flow={'443': 'service_HTTP'})
                    while not done:
                        action = agent.choose_action(observation)
                        observation_, reward, terminated, truncated = env.step(action)
                        done = terminated or truncated
                        score += reward
                        agent.store_transition(observation, action, reward, observation_, done)
                        agent.learn()
                        observation = observation_
                        # print('ob: ' ,observation)
                        # print('action : ',action)

                        if done:
                            break
                    print('action : ',action)


                    avg_score = np.mean(scores[:])
                    avg_scores.append(avg_score)
                    scores.append(score)
                    eps_history.append(agent.epsilon)
                    avg_score = np.mean(scores[-100:])
                    print('Episode', i + 1, 'Score: %.2f Training' % score, 'average Score: %.2f' % avg_score,'Epsilon: %.2f' % agent.epsilon)

            except KeyboardInterrupt:
                print("Fin du programme")
                break
        x = [i + 1 for i in range(len(scores))]
        filename = 'Sdwan.png'
        plotLearning(x, scores, eps_history, avg_scores, filename)
