import os, serial, serial.tools.list_ports, threading, logging, sys
import Node, Hub
from Ledger import Packet
from Node import PType
from datetime import datetime

def purge_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

class TUI():
    def __init__(self, node = None):
        self.node = node

    def show(self):
        options = []
        options.append(["Run", self.dashboard_show])
        if(self.node.__class__.__name__ == "Sensor"):
            options.append(["SNR request to connected hub", self.snr_exchange_show])
        elif(self.node.__class__.__name__ == "Hub"):
            options.append(["Show packet history", self.packet_history_show])
        options.append(["Listen for MAC packets", self.listen_oneshot_show])
        options.append(["Send a MAC packet", self.send_query_show])
        options.append(["Board configuration", self.board_config_show])
        options.append(["MAC configuration", self.mac_config_show])
        options.append(["Terminal interface", self.terminal_show])
        options.append(["Flush input buffer", self.input_buffer_show])
        options.append(["Flush input buffer - raw", self.raw_input_buffer_show])

        inp = ""
        while(inp != "x"):
            purge_terminal()
            print("===== {} command interface ({}) =====".format(self.node.__class__.__name__,self.node.interface.s.port.upper()))
            for i in range(len(options)):
                print(str(i+1) + ". " + options[i][0])
            print("Press x to exit\n")
            inp = input(">")
            if(inp.isnumeric() and int(inp) in range(1,len(options)+1)):
                self.node.interface.read_raw()  # Flush the input buffer or uncaught board communication will disrupt program
                options[int(inp)-1][1]()

    def dashboard_show(self):
        purge_terminal()
        self.node.STOP = False
        print("[Use KeyboardInterrupt to stop]")
        # Stupid hack
        try:
            self.node.run()
        except KeyboardInterrupt:
            pass
        self.node.STOP = True
        input("Press ENTER to continue")

    def board_config_show(self):
        options = []
        options.append(["Spreading factor", "sf", "(sf7 to sf12)"])
        options.append(["Code rate", "cr", "(4/5,4/6,4/7,4/8)"])
        options.append(["Power level", "pwr", "(-3 to 15)"])
        options.append(["Bandwidth", "bw", "(125,250,500)"])
        options.append(["Watchdog timer", "wdt", "unsigned 32 bit integer (milliseconds)"])

        inp = ""
        while(inp != "x"):
            purge_terminal()
            print("Current configuration:")
            for i in range(len(options)):
                print("{}. {}".format(str(i+1), options[i][0]).ljust(25) + str(getattr(self.node,options[i][1].upper())).ljust(10) + options[i][2])
            print("Press x to return\n")
            inp = input(">")
            if(inp.isnumeric() and int(inp) in range(1,len(options)+1)):
                val = input("Enter new value>")
                self.node.set_param(options[int(inp)-1][1], val)

    def mac_config_show(self):
        options = []
        options.append(["Adress", "mac_adr", "String (length 2)"])
        options.append(["Version", "mac_ver", "Binary (length 2)"])

        inp = ""
        while(inp != "x"):
            purge_terminal()
            print("Current configuration:")
            for i in range(len(options)):
                print("{}. {}".format(str(i+1), options[i][0]).ljust(25) + str(getattr(self.node,options[i][1].upper())).ljust(10) + options[i][2])
            print("Press x to return\n")
            inp = input(">")
            if(inp.isnumeric() and int(inp) in range(1,len(options)+1)):
                val = input("Enter new value>")
                if(options[int(inp)-1][0] == "Adress"):
                    self.node.set_adress(val)
                elif(options[int(inp)-1][0] == "Version"):
                    self.node.set_version(val)

    def send_query_show(self):
        purge_terminal()
        print("Enter MAC payload")
        payload = input(">")
        packet = self.node.build_packet(ptype=PType.DATA_UP, destination='00', payload=payload)  #Uses wildcard '00' all-nodes destination
        self.node.send_mac(packet)
        input("Press ENTER to continue")

    def snr_exchange_show(self):
        purge_terminal()
        print("[Use KeyboardInterrupt to stop]")
        if (self.node.__class__.__name__ != "Sensor" or self.node.connected_hub == None):
            print("No hub is connected to this node, using '00'")
            self.node.connected_hub = "00"
        # Stupid hack
        try:
            f = open('snrlog.txt', 'a')
            packet = self.node.build_packet(ptype=Node.PType.AUTOSET, destination=self.node.connected_hub, payload="begin")
            self.node.send_mac(packet)
            while(True):
                packet_rx = self.node.listen_mac()   # Returns only packets with correct destination adress
                if(packet_rx != None and packet_rx.type == PType.AUTOSET):
                    logging.info(packet_rx.payload)
                    f.write(str(datetime.now()) + "," + packet_rx.payload +"\n")
                autoset_ping = self.node.build_packet(ptype = PType.AUTOSET, destination=self.node.connected_hub, payload="")
                self.node.send_mac(autoset_ping)
        except KeyboardInterrupt:
            f.close()
            
        
        
    def packet_history_show(self):
        purge_terminal()
        print("Last {} packets:".format(str(self.node.ledger.HIST_SIZE)))
        for packet in self.node.ledger.pkt_hist:
            print(packet)
        input("Press ENTER to continue")
    
    def listen_oneshot_show(self):
        purge_terminal()
        print("Listening for MAC packets ...")
        packet = self.node.listen_mac()
        if(packet is not None):
            print(packet.payload)
        input("Press ENTER to continue")

    def terminal_show(self):
        purge_terminal()
        print("Enter command for board")
        print("Press x to return")
        inp = input(">")
        while(inp != "x"):
            response = self.node.interface.send(inp)
            if(response != True):
                print(response)
            in_buffer = self.node.interface.read_input_buffer()
            if(len(in_buffer) > 0):
                for elem in in_buffer:
                    print(str(elem))
            inp = input(">")

    def input_buffer_show(self):
        purge_terminal()
        in_buffer = self.node.interface.read_input_buffer()
        for elem in in_buffer:
            print(elem)
        input("Press ENTER to continue")

    def raw_input_buffer_show(self):
            purge_terminal()
            raw = self.node.interface.read_raw()
            print(raw)
            input("Press ENTER to continue")
