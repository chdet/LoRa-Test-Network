import serial, serial.tools.list_ports , time, logging
from NodeInterface import NodeInterface
from Ledger import Packet, Ledger
from enum import Enum
from threading import Thread

WAIT_TO_SEND = 0.1          # Nodes wait a set amount of time before responding to a message to avoid missing the response window

class PType():
    DATA_UP = '000'
    ACK = '001'
    JOIN = '010'
    AUTOSET = '011'

class Node(Thread):
    def __init__(self, COM_port):
        super().__init__()      #Initializes the threading functionality
        self.interface = NodeInterface(COM_port)
        response = self.interface.send("mac pause")
        if(response == "0"):
            raise RuntimeError("The mac layer could not be paused on the board, exiting immediately.")
        node_config = self.interface.get_configuration()
        self.ledger = Ledger()
        self.SF = node_config["sf"]
        self.CR = node_config["cr"]
        self.PWR = int(node_config["pwr"])
        self.BW = node_config["bw"]
        self.WDT = node_config["wdt"]
        self.MAC_ADR = "00"
        self.MAC_VER = "00"
        self.STOP = True

    def run(self):
        #To be redefined in inheritance
        pass

    def listen_mac(self):
        """ Polls the LoRa board for MAC packets and returns only packets intended for Node  """
        
        logging.debug("Entering listen_mac()")
        done = False
        while(done == False):
            serial_inp = self.interface.listen(timeout = float(self.WDT)/1000)    # Should allow differentiation between no packets and reception error (doesn't work)
            if(serial_inp == False):
                logging.warning("Listening error: board is busy")
                done = True
            elif(serial_inp is not None and serial_inp[0:8] == "radio_rx"):
                try:
                    packet = Packet().fromframe(bytes.fromhex(serial_inp[8:].strip()))
                    if(packet.version == self.MAC_VER and packet.destination_adress in (self.MAC_ADR,'00')):
                        return packet
                except UnicodeDecodeError:
                    logging.error("Packet error: could not interpret packet")
            elif(serial_inp is not None):
                #TODO: WDT timeout shouldn't be logged, sohuld find a way to differentiate without missing true errors (low priority)
                # logging.warning("Listening error: " + serial_inp)
                done = True
        return None

    def send_mac(self, packet):
        """ Sends a MAC packet to the board for transmission
        
            Argument:
                mac_frame -- bytes object
        """
        logging.debug("Entering send_mac()")
        if(packet is not None):
            serial_packet = "radio tx " + packet.build_frame().hex()
            response = self.interface.send(serial_packet)
            if(response != True):
                logging.warning("Sending error: " + response)
            else:
                if(self.SF == "sf7"):
                    # Workaround, see buglist
                    time.sleep(0.05)
                    serial_input = self.interface.read_input_buffer()
                    for elem in serial_input:
                        logging.debug(elem)      
                elif(self.interface.wait_for_serial()):
                    serial_input = self.interface.read_input_buffer()
                    for elem in serial_input:
                        logging.debug(elem)

    def build_packet(self, ptype, destination, payload, req_ack = False):
        packet = Packet(version = self.MAC_VER, _type=ptype, req_ack=req_ack, destination=destination,
                        source=self.MAC_ADR, payload=payload)
        return packet

    def set_version(self,value):
        try:
            int(value,2)
            self.MAC_VER = value
        except ValueError:
            pass
    
    def set_adress(self,value):
        if(len(value) <= 2):
            self.MAC_ADR = value

    def set_param(self, param, value):
        response = self.interface.send("radio set {} {}".format(str(param),str(value)))
        if (response == True):
            setattr(self, str(param).upper(), value)
            return True
        else:
            return False

