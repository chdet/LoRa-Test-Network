import logging, time
from Node import Node, PType, WAIT_TO_SEND

class Hub(Node):
    def __init__(self, COM_port):
        super().__init__(COM_port)

    def run(self):
        logging.info("Hub now online")
        logging.info("Now listening for MAC packets ...")
        while(self.STOP == False):
            packet_rx = self.listen_mac()
            if(packet_rx != None and self.ledger.busy_with in (packet_rx.source_adress, None)):
                #TODO: Add timeout on exclusive access
                logging.info("Received packet from {}".format(packet_rx.source_adress))
                self.ledger.push_history(packet_rx)
                self.process_packet(packet_rx)
                logging.info("Now listening for MAC packets ...")

    def process_packet(self, packet):
        """ Performs appropriate action depending on packet type  """

        if packet.req_ack:
            # This hub seems pretty easy to DDOS doesn't it ?
            logging.info("Sending ACK")
            response = self.build_packet(ptype=PType.ACK, destination=packet.source_adress, payload="")
            time.sleep(WAIT_TO_SEND)
            self.send_mac(response)

        if packet.type == PType.DATA_UP:
            logging.info("Received {}".format(packet.payload))
            if(packet.source_adress in self.ledger.adresses):
                self.ledger.data[packet.source_adress].append(packet.payload)   
            # There is no entry corresponding to the adress if it hasn't joined, ignore
        elif packet.type == PType.ACK:
            logging.info("Received ACK")
        elif packet.type == PType.JOIN:
            # Join process is required to ensure that no two nodes send from the same adress, which would result in 
            # inaccruate data collecting. In a secured network it would also provide authentication.
            logging.info("Received join request")
            if(packet.source_adress in self.ledger.adresses):
                logging.info("{} is already connected".format(packet.source_adress))
                response = self.build_packet(ptype=PType.JOIN, destination=packet.source_adress, payload="already connected")
                time.sleep(WAIT_TO_SEND)
                self.send_mac(response)
            else:
                self.ledger.add(packet.source_adress)
                response = self.build_packet(ptype=PType.JOIN, destination=packet.source_adress, payload="ok")
                time.sleep(WAIT_TO_SEND)
                self.send_mac(response)
                logging.info("{} is now connected".format(packet.source_adress))
        elif packet.type == PType.AUTOSET:
            if(packet.payload == "begin"):
                logging.info("Received autoset request, starting ...")
                self.ledger.busy_with = packet.source_adress 
            if(packet.payload == "done"):
                logging.info("Autoset done")
                self.ledger.busy_with = None
            else:
                measured_snr = self.interface.get_snr()
                response = self.build_packet(ptype=PType.AUTOSET, destination=packet.source_adress, payload=("snr="+measured_snr))
                time.sleep(WAIT_TO_SEND)
                logging.info("Sending SNR info")
                self.send_mac(response)
        else:
            logging.warning("Unknown packet type: " + packet.type)