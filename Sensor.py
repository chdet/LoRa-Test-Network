import time, logging
from Node import Node, PType, WAIT_TO_SEND

class Sensor(Node):
    def __init__(self, COM_port):
        super().__init__(COM_port)
        self.connected_hub = None
        self.autoset_done = False
        self.snr_threshold = {'sf7':0, 'sf8':-3, 'sf9': -5, 'sf10':-8, 'sf11':-9, 'sf12':-12}
        self.snr_down = -3
        self.snr_up = 15

    def run(self):
        logging.info("Sensor now online")
        while(self.STOP == False):
            if(self.connected_hub is None):
                self.set_param("pwr", 15)
                if(self.connect() == False):
                    break
                time.sleep(WAIT_TO_SEND)
                if(self.init_autoset() ==  False):
                    break
            if(self.autoset_done == False):
                packet_rx = self.listen_mac()
                if(packet_rx != None):
                    logging.info("Received packet from {}".format(packet_rx.source_adress))
                    self.process_packet(packet_rx)
                elif(packet_rx == None):
                    dummy_packet = self.build_packet(ptype=PType.AUTOSET, destination=self.MAC_ADR, payload=("snr=-50"))
                    self.process_packet(dummy_packet)
            else:
                logging.info("Sending sensor data to hub")
                data = "All your bases are belong to us!"
                message = self.build_packet(ptype = PType.DATA_UP, destination=self.connected_hub, payload=data)
                self.send_mac(message)
                packet_rx = self.listen_mac()
                if(packet_rx != None):
                    logging.info("Received packet from {}".format(packet_rx.source_adress))
                    self.process_packet(packet_rx)
                logging.info("Entering sleep mode")
                time.sleep(5)

    def connect(self):
        logging.info("No hub is currently connected, sending request ...")
        conn_req = self.build_packet(ptype = PType.JOIN, destination='00', payload="")  # Wildcard '00' adress
        tries = 0
        while(self.connected_hub == None and tries < 2):
            self.send_mac(conn_req)
            packet_rx = self.listen_mac()   # Returns only packets with correct destination adress
            if(packet_rx is not None):
                self.process_packet(packet_rx)
            if(self.connected_hub == None):
                logging.info("No response, trying again ...")
                tries = tries + 1
        if(self.connected_hub == None):
            logging.warning("No hub has responded on this channel, exiting now.")
            return False   
        else:
            logging.info("Connected to hub <{}>".format(self.connected_hub))
            return True


    def init_autoset(self):
        self.autoset_done = False
        logging.info("Starting autoset")
        autoset_req = self.build_packet(ptype = PType.AUTOSET, destination=self.connected_hub, payload="begin")
        tries = 0
        while(tries < 2):
            self.send_mac(autoset_req)
            packet_rx = self.listen_mac()   # Returns only packets with correct destination adress
            if(packet_rx != None and packet_rx.type == PType.AUTOSET):
                # self.process_packet(packet_rx)                                # First packet is not processed as it is sent at max power
                self.set_param("pwr", round((self.snr_up+self.snr_down)/2))
                autoset_ping = self.build_packet(ptype = PType.AUTOSET, destination=self.connected_hub, payload="")
                time.sleep(WAIT_TO_SEND)
                self.send_mac(autoset_ping)
                return True
            elif(packet_rx != None):
                self.process_packet(packet_rx)
            else:
                logging.info("No response, trying again ...")
                tries = tries + 1
        logging.warning("No response to autoset request, exiting now.")
        return False


    def stop_autoset(self):
        conn_req = self.build_packet(ptype = PType.AUTOSET, destination=self.connected_hub, payload="done")
        time.sleep(WAIT_TO_SEND)
        self.send_mac(conn_req)
        self.snr_up = 15
        self.snr_down = -3
        self.autoset_done = True
        logging.info("Autoset done, pwr = " + str(self.PWR))

    def continue_autoset(self):
        snr_req = self.build_packet(ptype = PType.AUTOSET, destination=self.connected_hub, payload="")
        time.sleep(WAIT_TO_SEND)
        self.send_mac(snr_req)

    def process_packet(self, packet):
        """ Performs appropriate packet processing  """

        if packet.req_ack:
            # This hub seems pretty easy to DDOS doesn't it ?
            response = self.build_packet(ptype=PType.ACK, destination=packet.source_adress, payload="")
            time.sleep(WAIT_TO_SEND)
            self.send_mac(response)

        if packet.type == PType.DATA_UP:
            pass
        elif packet.type == PType.ACK:
            #TODO: Add ACK handling
            pass
        elif packet.type == PType.JOIN:
            if(packet.payload == "ok"):
                self.connected_hub = packet.source_adress
            elif(packet.payload == "already connected"):
                #TODO: Handle the "already connected case"
                self.connected_hub = packet.source_adress
        elif packet.type == PType.AUTOSET:
            threshold = self.snr_threshold[self.SF]
            snr = int(packet.payload.split("=")[1])
            logging.info("Autoset response - snr = " + str(snr))
            if(snr in [threshold, threshold + 1]):
                self.stop_autoset()
            elif(self.snr_up == self.snr_down+1):
                if(snr > threshold):
                    self.set_param("pwr", self.snr_down)
                    self.stop_autoset()
                elif(self.snr_down == 14):
                    self.set_param("pwr", self.snr_up)
                    self.stop_autoset()
                else:
                    self.snr_down = self.snr_up
                    self.snr_up = 15
                    self.set_param("pwr", round((self.snr_up+self.snr_down)/2))
                    self.continue_autoset()
            elif(snr < threshold):
                self.snr_down = round((self.snr_up+self.snr_down)/2)
                self.set_param("pwr", round((self.snr_up+self.snr_down)/2))
                self.continue_autoset()
            elif(snr > threshold):
                self.snr_up = round((self.snr_up+self.snr_down)/2)
                self.set_param("pwr", round((self.snr_up+self.snr_down)/2))
                self.continue_autoset()
        else:
            logging.warning("Unknown packet type: " + packet.type)
    