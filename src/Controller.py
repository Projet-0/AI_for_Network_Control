"""Module Controller Manage Controller thread and communicate with AI thread."""

import time
import sys
import signal
import logging

import numpy
import NetPBR as npr

IP_CLIENT_NET = "192.168.4.0"
IP_SERVER_ABING = "192.168.202.6"


def collect_notraffic(sdw_connect, ip_dest):
    """Function collect data without generate traffic."""
    int_1_collect = npr.get_int("sdwan2_1", "Gi1/0/24", sdw_connect)
    int_2_collect = npr.get_int("sdwan2_2", "Gi1/0/24", sdw_connect)
    latency_collect = npr.get_latency_3(ip_dest)
    logging.info("collect_notraffic -> latency = " + str(latency_collect))
    return int_1_collect,int_2_collect,latency_collect

class StageController:
    """Class representing a Controller thread"""
    def __init__(self):
        logging.basicConfig(filename="src/logs/Controller.log",
                             level=logging.INFO,
                             format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        signal.signal(signal.SIGINT, self.signal_handler)
        self.SetACL = False
        self.end = False
        self.latency_data = [1, 1, 1 , 1 , 1, 1, 1, 1, 1]
        self.idx = 0

    def signal_handler(self, sig, frame):
        """Function manage SIGINT signal."""
        print('You pressed Ctrl+C!')
        print(sig)
        print(frame)
        self.end = True
        sys.exit(0) # To be remove

    def switchmode(self, msg = None):
        """Function to permut ACL mode."""
        if (msg): # Set ACL state according to msg
            lst_port = msg.split('|')
            if (lst_port == [] or lst_port[0] == "NOACL"):
                self.SetACL = False
                logging.info("ACL Unset (mode 0) (" + str(self.SetACL) + ")")
            else:
                self.SetACL = True
                logging.info("ACL Set (mode 0) (" + str(self.SetACL) + ")" )
        else: # Switch ACL state
            if (self.SetACL):
                self.SetACL = False
                logging.info("ACL Unset (mode 1) (" + str(self.SetACL) + ")")
                lst_port = ["NOACL"]
            else:
                self.SetACL = True
                logging.info("ACL Set (mode 1) (" + str(self.SetACL) + ")" )
                lst_port = ["80", "443"]
        return lst_port

    def sendcmd(self, sdw_lst : list, nbacl:int, interfaces:list, options:list ,addr_src:list, mask_src:list, addr_dst:list, mask_dst:list, lst_port:list):
        """Function to call NetPBR to set ACL according to AI request."""
        for i in range(len(sdw_lst)):
            npr.set_ACL(sdw_lst[i], nbacl, interfaces[i],
                        option = options,
                        cisco_addr_src = addr_src[i],
                         cisco_mask_src = mask_src[i],
                         cisco_addr_dst = addr_dst[i],
                         cisco_mask_dst = mask_dst[i],
                         ports=lst_port)
        # npr.set_ACL(sdw1_connect, 101, cisco_addr_src = IP_CLIENT_NET,
        #  cisco_mask_src = "0.0.0.255", ports=lst_port)
        # npr.set_ACL(sdw2_connect, 102, cisco_addr_src = "0.0.0.0",
        #  cisco_mask_src = "255.255.255.255", ports=lst_port)


    def stageCTR(self, queueSCTR, queueSAI):
        """Function where Controller thread is start."""
        print("stage1")

        while not self.end:
            # Check if Request is receive
            sdw1_connect = npr.create_ssh(1)
            sdw2_connect = npr.create_ssh(2)
            lst_port = []

            # Perform Action
            if not queueSAI.empty():
                msg = queueSAI.get()    # get msg from SAI
                logging.info("msg = " + str(msg))
                logging.info("str(msg).isnumeric() = " + str(str(msg).isnumeric()) + " msg==1" + str(msg==1))
                if (msg == "update lists"):
                    #print("! ! ! SController RECEIVED from SAI:", msg)
                    print('')
                elif(str(msg).isnumeric() and int(msg)==1): # switch mode
                    lst_port = self.switchmode()
                    logging.info("Switched mode -> lst_port = " + str(lst_port))
                elif(not str(msg).isnumeric()) : # switch mode according to msg
                    lst_port = self.switchmode(msg)
                    logging.info("Switched mode (w. msg) -> lst_port = " + str(lst_port))
                     ## example : 80|40

            # Send command with lst_port updated

            # self.sendcmd([sdw1_connect, sdw2_connect],
            #             101, ["Gi1/0/24", "Gi1/0/24"], [IP_CLIENT_NET, "0.0.0.0"],
            #              ["0.0.0.255", "255.255.255.255"], lst_port)
                
            
            if lst_port:
                if lst_port != ["NOACL"]:
                    logging.info("Set ACL via sendcmd")
                    self.sendcmd([sdw1_connect, sdw2_connect],
                            101, ["Gi1/0/24", "Gi1/0/24"],
                            ["eq", "eq", "gt"],
                            [IP_CLIENT_NET, "any"],["0.0.0.255", " "],
                            ["any", "any"],[" ", " "],
                            lst_port)
                else:
                    logging.info("Unset ACL via sendcmd")
                    self.sendcmd([sdw1_connect, sdw2_connect],
                            101, ["Gi1/0/24", "Gi1/0/24"],
                            [],
                            [IP_CLIENT_NET, "any"],["0.0.0.255", " "],
                            ["any", "any"],[" ", " "],
                            ["NOACL"])
            else :
                logging.info("No need to send cmd to SDWAN")
            # self.sendcmd([sdw1_connect],
            #               101, ["Gi1/0/24"], [IP_CLIENT_NET],
            #                ["0.0.0.255"], lst_port)

            time.sleep(1) # work

            # Collect & Prepare Data
            pre_queue = ""
            lst_service_channel = []
            throughput_input = [-1, -1]
            throughput_output = [-1, -1]
            pck_loss = [-1.0, -1.0]
            latency_avg = -1
            latency_sigma = -1
            latency_max = -1
            bandwidth = -1
            try:
                int_1, int_2, latency = collect_notraffic(sdw1_connect, IP_SERVER_ABING)
                if int_1["I_rate_bit"] and int_2["I_rate_bit"]:
                    throughput_input[0] = int_1["I_rate_bit"]
                    throughput_input[1] = int_2["I_rate_bit"]
                if int_1["O_rate_bit"] and int_2["O_rate_bit"]:
                    throughput_output[0] = int_1["O_rate_bit"]
                    throughput_output[1] = int_2["O_rate_bit"]
                if int_1["O_drop"] and int_2["O_drop"]:
                    pck_loss[0] = int_1["O_drop"]
                    pck_loss[1] = int_2["O_drop"]
                if latency:
                    logging.info("latency = " + str(latency))
                    bandwidth = latency["ABw"]
                    if self.idx == 9:
                        self.idx = 0
                    self.latency_data[self.idx] = float(latency["RTT-min"])
                    self.latency_data[self.idx+1] = float(latency["RTT-avg"])
                    self.latency_data[self.idx+2] = float(latency["RTT-max"])
                    self.idx += 3
                    logging.info("latency_data = " + str(self.latency_data))
                    latency_avg = numpy.average(self.latency_data)
                    latency_sigma = numpy.std(self.latency_data)
                    latency_max = max(self.latency_data)
                pre_queue = str(str(lst_service_channel) + "|" + str(throughput_input) + "|" + str(throughput_output) + "|" + str(pck_loss) + "|"
                               + str(latency_avg)  + "|" + str(latency_sigma) + "|" + str(latency_max)  + "|"  + str(bandwidth))
                logging.info(pre_queue)
            except Exception as error:
                pre_queue = "ERR_DATA"
                logging.error(error)

            # Prepare Data

            # Send Data
            queueSCTR.put(pre_queue)
            npr.remove_ssh(sdw1_connect)
            npr.remove_ssh(sdw2_connect)
        print(self.end)
        queueSCTR.put('s1 is DONE')

if __name__ == "__main__":
    sdw01_connect = npr.create_ssh(1)
    sdw02_connect = npr.create_ssh(1)
    # int_01, int_02, latency0 = collect_notraffic(sdw01_connect, IP_SERVER_ABING)
    # print(int_01)
    # print(int_01)
    # print(latency0)
    npr.remove_ssh(sdw01_connect)
    npr.remove_ssh(sdw02_connect)
