"""Module that purpose function for managing cisco switch and testing network."""

import subprocess
from netmiko import ConnectHandler
from parse import parse
from libs import measure_latency

DEBUG = False

# Following IP need to be change
IP_abing_server = "192.168.202.6"


# ssh cisco@192.168.8.254
sdwan1 = {
    'device_type': 'cisco_ios',
    'host':   '192.168.201.1', #  192.168.4.1 192.168.8.254
    'username': 'cisco',
    'password': 'ping123',
    # 'port' : 22,          # optional, defaults to 22
    'secret': 'ping123',     # optional, defaults to ''
    "session_log": 'src/logs/netmiko_session1.log',
    "session_log_file_mode": "append"
}

# ssh cisco@192.168.8.218
sdwan2 = {
    'device_type': 'cisco_ios',
    'host':   '192.168.202.1', # 192.168.50.1
    'username': 'cisco',
    'password': 'ping123',
    # 'port' : 22,          # optional, defaults to 22
    'secret': 'ping123',     # optional, defaults to ''
    "session_log": 'src/logs/netmiko_session2.log',
    "session_log_file_mode": "append"
}

machine = ["sdwan1", "sdwan2"]
int_lst = ["Gi1/0/1", "Gi1/0/2"]
links = [["10.1.1.1", "10.2.3.2"], ["10.2.1.1", "10.3.3.2"],
          ["192.168.4.1", "192.168.8.218"]] #[src, dst], ...]
protocols = [
    ["Echo", [7]],
    ["FTP", [21,20]],
    ["SSH", [22]],
    ["Telnet", [23]],
    ["SMTP", [25]],
    ["TFTP", [69]],
    ["HTTP", [80, ]],
    ["POP", [109, 110]],
    ["SQL", [118]],
    ["IMAP", [143]],
    ["LDAP", [389]],
    ["HTTPS", [443]],
    ["TLS-SSL", [465]],
    ["DHCPS", [546, 547]],
    ["IMAPS", [585]],
    ["SMTP", [587]],
    ["LDAPS", [636]],
    ["Cisco", [5004]] # UDP
]



def get_int(cisco_name, cisco_interface, sdw_connect):
    """Function to get information about interfaces."""
    cmd = "sh int " + cisco_interface + " | inc drops|bits"
    cisco_output = list((sdw_connect.send_command(cmd)).split('\n'))
    for j in range(len(cisco_output)):
        cisco_output[j] = cisco_output[j].strip()

    cisco_int = {
    "cisco_name" : "SDWAN99",
    "cisco_interface" : "fa0/0",
    "size_I_queue" : -1,
    "max_I_queue" : -1,
    "drops_I_queue" : -1,
    "flushes_I_queue" : -1,
    "O_drop" : -1,
    "I_rate_bit" : -1,
    "I_rate_packet" : -1,
    "O_rate_bit" : -1,
    "O_rate_packet" : -1,
    "Unknown_protocol" : -1
    }
    template = ["Input queue: {}/{}/{}/{} (size/max/drops/flushes); Total output drops: {}",
  "5 minute input rate {} bits/sec, {} packets/sec",
  "5 minute output rate {} bits/sec, {} packets/sec",
     "{} unknown protocol drops"]

    parsed = []
    data = []
    for i in range(len(template)):
        # print(cisco_output[i])
        parsed.append(parse(template[i], cisco_output[i]))
    # print(list(parsed[0].fixed))
    if (parsed[0] is not None):
        for i in range(len(parsed)):
            data0 = list(parsed[i].fixed)
            for j in range(len(data0)):
                data.append(data0[j])
    else :
        print("error with " + cisco_name + " " + cisco_interface)
        print(cisco_output)
        return -1

    # print(data)
    cisco_int["cisco_name"] = cisco_name
    cisco_int["cisco_interface"] = cisco_interface
    cisco_int["size_I_queue"] = data[0]
    cisco_int["max_I_queue"] = data[1]
    cisco_int["drops_I_queue"] = data[2]
    cisco_int["flushes_I_queue"] = data[3]
    cisco_int["O_drop"] = data[4]
    cisco_int["I_rate_bit"] = data[5]
    cisco_int["I_rate_packet"] = data[6]
    cisco_int["O_rate_bit"] = data[7]
    cisco_int["O_rate_packet"]  = data[8]
    cisco_int["Unknown_protocol"] = data[9]
    return cisco_int

# Lien haut : SDWAN1 (10.1.1.1) <-> ... <-> SDWAN2 (10.2.3.2) : ping ip 10.2.3.2 source 10.1.1.1
# Lien bas : SDWAN1 (10.2.1.1) <-> ... <-> SDWAN2 (10.3.3.2) : ping ip 10.3.3.2 source 10.2.1.1
def get_latency(cisco_name, cisco_addr_src, cisco_addr_dest, sdw_connect):
    """
    Return parse of ping request
    """
    cmd = "ping ip " + cisco_addr_dest + " source " + cisco_addr_src
    cisco_output = list((sdw_connect.send_command(cmd)).split('\n'))
    for j in range(len(cisco_output)):
        cisco_output[j] = cisco_output[j].strip()

    cisco_ping = {
    "cisco_name" : "SDWAN99",
    "cisco_addr_src" : "10.0.0.0",
    "cisco_addr_dest" : "10.0.0.0",
    "nb_packet_sent" : -1,
    "size_ICMP_packet" : -1,
    "timeout" : -1,
    "Success_rate_percent" : -1,
    "Success_packet" : -1,
    "round_trip_min" : -1,
    "round_trip_avg" : -1,
    "round_trip_max" : -1
    }
    template = ["Type escape sequence to abort.",
    "Sending {}, {}-byte ICMP Echos to {}, timeout is {} seconds:",
    "Packet sent with a source address of {}",
    "!!!!!",
    "Success rate is {} percent ({}/{}), round-trip min/avg/max = {}/{}/{} ms"
    ]
    parsed = []
    data = []
    for i in range(len(template)):
        # print(cisco_output[i])
        # print(template[i])
        parsed.append(parse(template[i], cisco_output[i]))
    # print(list(parsed[0].fixed))
    # print(parsed[0])
    for i in range(len(parsed)):
        if (parsed[i] is None):
            continue
        data0 = list(parsed[i].fixed)
        for j in range(len(data0)):
            data.append(data0[j])

    # print(data)
    cisco_ping["cisco_name"] = cisco_name
    cisco_ping["cisco_addr_src"] = cisco_addr_src # =data[2]
    cisco_ping["cisco_addr_dest"] = cisco_addr_dest # =data[4]
    cisco_ping["nb_packet_sent"] = data[0] # = data[7]
    cisco_ping["size_ICMP_packet"] = data[1]
    cisco_ping["timeout"] = data[3]
    cisco_ping["Success_rate_percent"] = data[5]
    cisco_ping["Success_packet"] = data[6]
    cisco_ping["round_trip_min"] = data[8]
    cisco_ping["round_trip_avg"]  = data[9]
    cisco_ping["round_trip_max"] = data[10]
    return cisco_ping

    # ACL = "access-list 102 permit ip " + cisco_addr_src + " " + cisco_mask_src
    # +" " + cisco_addr_dest + " " + cisco_mask_dest

def get_latency_2(cisco_addr_dest):
    """
    Return of tcplatency request
    """
    return measure_latency(host=cisco_addr_dest, runs=1, timeout=2)

def get_latency_3(cisco_addr_dest):
    """
    Return parse of abing request (https://github.com/RichardWithnell/abing)
    This function is not
    """
    abing = {
    "ID" : "SDWAN99",
    "addr_dest" : "10.0.0.0",
    "ABw" : -1,
    "Xtr" : -1,
    "DBC" : -1,
    "RTT-min" : -1,
    "RTT-avg" : -1,
    "RTT-max" : -1,
    "RTT-timeout" : -1,
    }
    latency_3 = ""
    
    DEBUG=False
    if not DEBUG:
        latency_3_str = subprocess.run(['./src/libs/abing', '-d', IP_abing_server, "-t", "1", "-n","1"], stdout=subprocess.PIPE, check=False)
        
        #/home/user/Downloads/abing-master/Bin/x86_64
        #print("latency debug",latency_3_str)
        latency_3 = latency_3_str.stdout
        latency_3 = latency_3.decode("utf-8")
    else:
        latency_3 = """1686830131 T: 192.168.50.9 ABw-Xtr-DBC:  10.7   0.4  11.1 ABW:  10.7 Mbps RTT: 7.322 7.550 7.913 ms 20 20
    1686830131 F: 192.168.50.9 ABw-Xtr-DBC:   9.7   0.1   9.8 ABW:   9.7 Mbps RTT: 7.322 7.550 7.913 ms 20 20"""
    # print(latency_3)
    latency_3 = list(latency_3.split('\n'))
    for j in range(len(latency_3)):
        latency_3[j] = latency_3[j].strip()

    template = ["{} T: {} ABw-Xtr-DBC:  {}   {}  {} ABW:  {} Mbps RTT: {} {} {} ms {} {}",
                "{} F: {} ABw-Xtr-DBC:   {}   {}  {} ABW:   {} Mbps RTT: {} {} {} ms {} {}"]
    parsed = []
    data = []
    for i in range(len(template)):
        # print(cisco_output[i])
        # print(template[i])
        parsed.append(parse(template[i], latency_3[i]))
    # print(list(parsed[0].fixed))
    # print(parsed[0])
    for i in range(len(parsed)):
        if (parsed[i] is None):
            continue
        data0 = list(parsed[i].fixed)
        for j in range(len(data0)):
            data.append(data0[j])
    #print("abing from data",data)
    
    abing["ID"] = data[0]
    abing["addr_dest"] = data[1]
    abing["ABw"] = data[2]
    abing["Xtr"] = data[3]
    abing["DBC"] = data[4]
    abing["RTT-min"] = data[6]
    abing["RTT-avg"] = data[7]
    abing["RTT-max"] = data[8]
    abing["RTT-timeout"] = data[9]

    return abing


def set_ACL(sdw_connect, nb_ACL:int, interface:str , option ,cisco_addr_src = "-1", cisco_mask_src = "-1", cisco_addr_dst = "-1", cisco_mask_dst="-1", ports=None):
    """
    this function set ACL on cisco router
    """
    acl1_0 = "no access-list " + str(nb_ACL)
    # print(str(sdw_connect) + str(nb_ACL) + str(interface) + str(option) + str(cisco_addr_src) + str(cisco_mask_src) + str(cisco_addr_dst) + str(cisco_mask_dst) + str(ports))
    # print(str(ports == ["NOACL"]))
    # print(str(bool(not (cisco_addr_src == "-1" or cisco_mask_src == "-1" or cisco_addr_dst == "-1" or cisco_mask_dst == "-1" or ports is None) and (option))))

    if (ports == ["NOACL"]):
        list((sdw_connect.send_config_set(acl1_0)).split('\n')) # no access-list
        acl1_1 = "int " + interface
        acl1_2 = "no ip policy route-map test"
        acl1_3 = "exit"
        set_PBR_2(sdw_connect, "test", 101, -1) # "route-map " + name_pbr + " permit 10", "no match ip address " + str(nb_ACL)

        config_commands = [acl1_1, acl1_2, acl1_3]

        list((sdw_connect.send_config_set(config_commands)).split('\n')) # "int " + interface, "no ip policy route-map test", "exit"
        set_PBR_2(sdw_connect, "test", 101, -2) # "route-map " + name_pbr + " permit 10", "match ip address " + str(nb_ACL)

    elif bool(not (cisco_addr_src == "-1" or cisco_mask_src == "-1" or cisco_addr_dst == "-1" or cisco_mask_dst == "-1" or ports is None or option is None)):
        list((sdw_connect.send_config_set(acl1_0)).split('\n')) # no access-list

        set_PBR_2(sdw_connect, "test", 101, -1) # "route-map " + name_pbr + " permit 10", "no match ip address " + str(nb_ACL)

        config_commands = []
        for i in range(len(ports)):
            config_commands.append("access-list " + str(nb_ACL) + " permit tcp " + cisco_addr_src + " " + cisco_mask_src + " " + cisco_addr_dst + " " + cisco_mask_dst + " " + option[i] + " " + ports[i])
        list((sdw_connect.send_config_set(config_commands)).split('\n')) # access-list...

        set_PBR_2(sdw_connect, "test", 101, -2) # "route-map " + name_pbr + " permit 10", "match ip address " + str(nb_ACL)

        config_commands = ["int " + str(interface), "ip policy route-map test", "exit"]
        list((sdw_connect.send_config_set(config_commands)).split('\n'))#"int Gi1/0/2", "ip policy route-map test"


def unset_ACL(sdw_connect, nb_ACL):
    """
    this function unset ACL on cisco router
    """
    acl1_0 = "no access-list " + str(nb_ACL)
    send_config_set = [acl1_0]
    list((sdw_connect.send_config_set(send_config_set)).split('\n'))


def set_PBR(sdw_connect, cisco_interface, name_pbr, nb_ACL, addr_route):
    """
    This function set PBR configuration on an interface
    """
    config_commands = ["int " + cisco_interface, "no switchport", "ip policy route-map " + name_pbr, "exit",
            "route-map " + name_pbr + " permit 10", "match ip address " + str(nb_ACL), "set ip next-hop " + addr_route]
    list((sdw_connect.send_config_set(config_commands)).split('\n'))


def set_PBR_2(sdw_connect, name_pbr, nb_ACL, mode:int):
    """
    This function set PBR configuration on an interface
    """
    config_commands = []
    if mode == -1:
        config_commands = ["route-map " + name_pbr + " permit 10", "no match ip address " + str(nb_ACL)]
    elif (mode == -2):
        config_commands = ["route-map " + name_pbr + " permit 10", "match ip address " + str(nb_ACL)]
    else:
        config_commands = ["route-map " + name_pbr + " permit 10", "no match ip address "  + str(nb_ACL), "match ip address " + str(nb_ACL)]
    list((sdw_connect.send_config_set(config_commands)).split('\n'))


def unset_PBR(sdw_connect : ConnectHandler, cisco_interface, name_pbr, nb_ACL, addr_route):
    """
    This function remove previous PBR configuration on an interface
    """
    config_commands = ["int " + cisco_interface, "switchport", "no route-map " + name_pbr, "exit",
            "route-map " + name_pbr + " permit 10", "match ip address " + str(nb_ACL), "set ip next-hop " + addr_route]
    list((sdw_connect.send_config_set(config_commands)).split('\n'))



def create_ssh(nb_sdw : int):
    """
    Return ConnectHandler object to control cisco device
    """
    if (nb_sdw == 1):
        sdw1_connect = ConnectHandler(**sdwan1)
        sdw1_connect.enable()
        return sdw1_connect
    if (nb_sdw == 2):
        sdw2_connect = ConnectHandler(**sdwan2)
        sdw2_connect.enable()
        return sdw2_connect
    return 0

def remove_ssh(sdw_connect):
    """
    remove SSH connexion
    """
    sdw_connect.disconnect()

if __name__ == "__main__":
    C = get_latency_3("192.168.50.9")
    print(C)
