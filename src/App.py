"""Application Module that create an AI thread and a Controller thread."""

__author__ = 'Ayoub BOUASRIA'

from multiprocessing import Process, Queue
import Controller
import AI

if __name__ == '__main__':
    SController= Controller.StageController()
    SAI= AI.StageAI()

    # collection to AI communication
    queueSCTR = Queue()  # SController.stageCTR() writes to queueSCTR

    # AI to collection communication
    queueSAI = Queue()  # SAI.stageAI() writes to queueSAI

    # start AI as another process
    SAI = Process(target=SAI.stage4AI, args=(queueSCTR, queueSAI))
    SAI.daemon = True
    SAI.start()     # Launch the AI process

    SController.stageCTR(queueSCTR, queueSAI) # start sending stuff from s1 to s2
    SController.join() # wait till s2 daemon finishes
