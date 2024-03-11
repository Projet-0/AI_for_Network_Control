"""Module test, as it's name suggest, test NetPBR library"""
import unittest
import os
import NetPBR as npr

class TestNetwork(unittest.TestCase):
    """Class to test if network is available."""
    def test_ping_gateway(self):
        """Function to test if Controller is connnect to SDWAN1 and SDWAN2."""
        ip_dest = npr.sdwan1["host"]
        ip_dest2 = npr.sdwan2["host"]
        response1 = os.system("ping -c 1 " + ip_dest)
        response2 = os.system("ping -c 1 " + ip_dest2)
        self.assertTrue(response1 == 0)
        self.assertTrue(response2 == 0)

    def test_ssh_connexion(self):
        """Function to test if Controller can open SSH connexion to SDWAN1 and SDWAN2."""
        sdw1_connect = npr.create_ssh(1)
        sdw2_connect = npr.create_ssh(2)
        npr.remove_ssh(sdw1_connect)
        npr.remove_ssh(sdw2_connect)



class TestNetPBR(unittest.TestCase):
    """Class to test if NetPBR library."""
    sdw1_connect = None
    sdw2_connect = None

    @classmethod
    def setUpClass(cls):
        """Function to call at the begginning of tests."""
        cls.sdw1_connect = npr.create_ssh(1)
        cls.sdw2_connect = npr.create_ssh(2)

    @classmethod
    def tearDownClass(cls):
        """Function to call at the end of tests."""
        npr.remove_ssh(cls.sdw1_connect)
        npr.remove_ssh(cls.sdw2_connect)

    def test_acl(self):
        """Function to test if ACL can be set and unset."""
        npr.set_ACL(self.sdw1_connect, 102, npr.links[0][0], "0.0.0.255", [80])
        npr.unset_ACL(self.sdw1_connect, 102)
        cmd = "traceroute " + npr.links[0][1]
        cisco_output = list((self.sdw1_connect.send_command(cmd, read_timeout=75)).split('\n'))
        print(cisco_output)

        npr.set_ACL(self.sdw1_connect, 102, npr.links[0][0], "0.0.0.255", [80])
        npr.unset_ACL(self.sdw1_connect, 102)
        cmd = "traceroute " + npr.links[0][1]
        cisco_output = list((self.sdw1_connect.send_command(cmd, read_timeout=75)).split('\n'))
        print(cisco_output)

    def test_pbr_2(self):
        """Function to test if NetPBR can generate pbr rules."""
        npr.set_PBR_2(self.sdw1_connect, "Gi1/0/24", "test", -1)
        npr.set_PBR_2(self.sdw1_connect, "Gi1/0/24", "test", -2)

    def test_get_int(self):
        """Function to test if NetPBR can access cisco interfaces."""
        int_1_collect = npr.get_int("sdwan1_1", "Gi1/0/24", self.sdw1_connect)
        int_2_collect = npr.get_int("sdwan2_1", "Gi1/0/24", self.sdw2_connect)
        print(int_1_collect)
        print(int_2_collect)

    def test_get_latency(self):
        """Function to test if NetPBR can have differents value of latency."""
        # npr.get_latency()
        # npr.get_latency_2()
        latency_collect = npr.get_latency_3("192.168.50.9")
        print(latency_collect)



if __name__ == "__main__":
    unittest.main()
