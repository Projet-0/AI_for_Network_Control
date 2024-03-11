"""Module AI Manage AI thread and communicate with Controller thread."""

__author__ = 'Ayoub BOUASRIA'

import time
import ast
import logging

DEBUG = False

from DQN import Agent
from Utils import plotLearning
import gym
import numpy as np
from SdwanEnv import SDWANEnv
import time

agent = Agent(gamma=0.99, epsilon=1.0, batch_size=64, n_actions=2, eps_end=0.01,input_dims=[3], lr=0.001)
scores, eps_history,avg_scores = [], [], []
n_games = 50

class StageAI:
    """Class representing a AI thread"""
    def __init__(self):
        logging.basicConfig(filename="src/logs/AI.log",
            level=logging.INFO,
            format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
        logging.info("Init AI...")
        print("Init AI...")
        self.loop_nb = 0
        self.set_ACL = False
        self.lst_service_channel = None
        self.throughput_input = None
        self.throughput_output = None
        self.pck_loss = None
        self.latency_avg = None
        self.latency_sigma = None
        self.latency_max = None
        self.bandwidth = None
        self.bandwidth_before_after = None
        self.latency_avg_before_after = None

        self.action = None
        self.env = SDWANEnv()
        self.loop = True
        self.counter = 0 

    def pased_q_list(self, qlst):
        """Function to parse queue list send from Controler into data useful for AI."""
        # latency_sdw1_2_sdw2 = q_list[2]
        self.lst_service_channel = ast.literal_eval(qlst[0])
         # throughput_input by interface (bit/s) [Gi1/0/1, Gi1/0/2]
        self.throughput_input = ast.literal_eval(qlst[1])
        self.throughput_output = ast.literal_eval(qlst[2])
        self.pck_loss = ast.literal_eval(qlst[3])
        self.latency_avg = float(qlst[4])
        self.latency_sigma = float(qlst[5])
        self.latency_max = float(qlst[6])
        self.bandwidth = float(qlst[7])
        self.latency_avg_before_after = []
        self.bandwidth_before_after = []

    def stage4AI(self, queueS1, queueS2):
        """Function where AI thread is start."""
        print("stage2")
        k=0
        # We train the model
        self.train()
        modulo =0

        while True:
            # Check if Request is receive
            pre_queue = "update lists"
            
            msg = queueS1.get()    # wait till there is a msg from sController
            
            
            #print("Value of msg is ",msg)

            if msg == "ERR_CISCO":
                print("Cisco switch disconnect")
            elif msg == "ERR_DATA":
                print("Data not ready")
            elif msg == 's1 is DONE ':
                break # ends While loop
            elif(self.loop_nb == 0):
                pre_queue = "NOACL"
            else:
                # Perform Action
                q_list = msg.split('|')
                
                self.pased_q_list(q_list)
                if len(self.latency_avg_before_after) == 1:
                    self.latency_avg_before_after.append(self.latency_avg)
                    self.bandwidth_before_after.append(self.bandwidth)
                elif len(self.latency_avg_before_after) == 2:
                    self.latency_avg_before_after = []
                    self.bandwidth_before_after = []

                #print("- - - sAI RECEIVED from sController:")
                #print(self.lst_service_channel)
                #print(self.throughput_input) # by interface
                #print(self.throughput_output) # by interface
                #print(self.pck_loss) # by interface
                #print(self.latency_avg)
                #print(self.latency_sigma)
                #print(self.latency_max)
                #print(self.bandwidth)
                #print(len(self.latency_avg_before_after))
                if len(self.latency_avg_before_after) == 2:
                    print("latency Before - After" + str(latency_avg_before_after[0]-latency_avg_before_after[1]) )                    
                    print("bandwidth - After" + str(bandwidth_before_after[0]-bandwidth_before_after[1]) )
                # if network is not full do
                # pre_queue = "NOACL"
                # otherwise if you want  for example to reroute http (80) and https (443) do
                # pre_queue = "80|443|1000"
                
                # AI beginning
            
          
                score = 0
                done = False
                observation=self.env.reset(np.uniform(6,30),np.uniform(8,25),1,flow={'443':'service_HTTP'})
            
                if(modulo%2==0):
                    done=True
                    
                else:
                    print("The value of bandwith is :",self.bandwidth)
                    print("The value of latency is :",self.latency_avg)

                while not done: 
                    
                    
                    action = agent.choose_action(observation)
                    observation_, reward, terminated, truncated = self.env.step(action)
                    done = terminated or truncated
                    score += reward
                    agent.store_transition(observation, action, reward,
                                           observation_, done)
                    agent.learn()

                    # We go to the next observation 

                    observation = observation_
                    # on attribue aux champs l'action retenue
                    self.action = action
                    # time.sleep(0.6)
                    if done:
                        k+=1
                        break
                
                    print("action : ", action)

                modulo += 1  
                done = False   
                scores.append(score)
                #print("la taille de scores est :",scores)
                
                avg_score=np.mean(scores[:])
                avg_scores.append(avg_score)
                eps_history.append(agent.epsilon)
                

                print('episode ',k, 'score %.2f' % score,
                      'average score %.2f' % avg_score,
                      'epsilon %.2f' % agent.epsilon)
                      

                ## Link changes

                if self.action == 0:
                    print("On envoie sur ethernet")
                    pre_queue = "NOACL"
                    self.latency_avg_before_after = [self.latency_avg]
                    self.bandwidth_before_after = [self.bandwidth]                    
                else:
                    print("on envoie sur MPLS")
                    pre_queue = "80|443|1000"
                    self.latency_avg_before_after = [self.latency_avg]
                    self.bandwidth_before_after = [self.bandwidth]                    


                if DEBUG:
                    print("self.loop_nb :" + str(self.loop_nb))
                    if self.loop_nb % 2 == 0:
                        if self.set_ACL:
                            self.set_ACL = not self.set_ACL
                            self.latency_avg_before_after = [self.latency_avg]
                            self.bandwidth_before_after = [self.bandwidth]
                            # pre_queue = "80|443|1000"
                            # print("Set ACL for port 80 and 443 (2)...")
                            pre_queue = "NOACL"
                            print("No ACL")
                            logging.info("No ACL")
                        else:
                            self.set_ACL = not self.set_ACL
                            self.latency_avg_before_after = [self.latency_avg]
                            self.bandwidth_before_after = [self.bandwidth]
                            # pre_queue = "1"
                            pre_queue = "80|443|1000"
                            print("Switch ACL mode")
                            logging.info("Switch ACL mode")
                    else :
                        pre_queue = "0"
                        

            self.loop_nb +=1
            #time.sleep(1) # work
            if self.action ==1:
                print("passe sur MPLS")
                time.sleep(10)
            ## Send Request
            queueS2.put(pre_queue)
            print("Applied")
            
            
       
        x=[k+1 for k in range(len(scores))]
        print("trace de grapghe")
        filename='../Sdwan_train.png'
        plotLearning(x,scores,eps_history,avg_scores,filename)
        print('nb episodes total: ',len(scores))
        
            
            
# Add Train function 
    def train(self):
        print("On entraine le model")
        number_episode = 1200
        for episode in range(number_episode):
            print("itération :", episode )
            latency_avg = np.random.uniform(10, 25)
            bandwidth = np.random.uniform(6, 30)
            observation = self.env.reset(latency_avg, bandwidth, 1,flow={'443':'service_HTTP'})
            
            done = False
            score = 0
            while not done:
                action = agent.choose_action(observation)
                observation_, reward, terminated, truncated = self.env.step(action)
                
                done = terminated or truncated
                score += reward
                agent.store_transition(observation, action, reward,
                                           observation_, done)
                
                agent.learn()

                
                observation = observation_
                
            scores.append(score)
            avg_score=np.mean(scores[:])
            avg_scores.append(avg_score)
            eps_history.append(agent.epsilon)
        print("derniere valeur de epsilon :", agent.epsilon )



if __name__ == '__main__':
    print("Start AI")


    # If you want to run without  a SSH connection you can uncomment this section

    #from multiprocessing import Process, Queue
    #import Controller
    
    #SAI = StageAI()
    #
    #queueSCTR = Queue()
    #queueSAI = Queue()
    #SAI.stage4AI(queueSCTR, queueSAI)
