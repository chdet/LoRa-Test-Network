import logging

class Ledger():
    def __init__(self):
        self.adresses = []
        self.pkt_hist = []
        self.HIST_SIZE = 15
        self.busy_with = None   # Adress of node in active communicaiton
        self.data = {} 

    def push_history(self,packet):
        if(len(self.pkt_hist) >= self.HIST_SIZE):
            del self.pkt_hist[0]
        self.pkt_hist.append(packet)

    def add(self, adress):
        self.adresses.append(adress)
        self.data[adress] = []

class Packet():
    def __init__(self, version=None, _type=None, req_ack = False, destination=None, 
        source=None,payload=None):
        self.version = version
        self.type = _type
        self.req_ack = req_ack
        self.destination_adress = destination
        self.source_adress = source
        self.payload = payload

    def __str__(self):
        return("<Type:{}|Version:{}|Destination:{}|Source:{}|Payload:{}>".format(self.type, self.version, self.destination_adress, self.source_adress, self.payload))

    def build_frame(self):
        # Build a bytes object containing the input information, formatted following the 
        # defined MAC frame : [MAC_HDR : self.Type(3bits) self.Version(2bits) RFU(3 bits)][DST_ADR (2 bytes)][SRC_ADR (2 bytes)][MAC_self.PAYLOAD]
        # self.Type, self.version are string-represented binary values, self.destination_adress and self.payload contain string information

        # Max frame size is 255 bytes

        header = int(self.type + self.version + "000", 2)
        header_b = bytes([header])

        self.destination_adress_b = self.destination_adress.encode("utf8")
        self.source_adress_b = self.source_adress.encode("utf8")

        self.payload_b = self.payload.encode("utf8")

        frame = header_b + self.destination_adress_b + self.source_adress_b + self.payload_b

        if(len(frame) > 255):
            logging.error("Frame error: payload length exceeds max frame size")
            return None
        else:
            return frame

    @classmethod
    def fromframe(cls, frame):
        # Generate a new instance of Packet from a received frame

        packet = cls()  # Creates a new instance of Packet()
        header_b = frame[0]
        dst_adress_b = frame[1:3]
        src_adress_b = frame[3:5]
        payload_b = frame[5:]

        header_bin = format(header_b, "08b")
        packet.type = header_bin[0:3]
        packet.version = header_bin[3:5]

        packet.destination_adress = dst_adress_b.decode("utf8")
        packet.source_adress = src_adress_b.decode("utf8")
        packet.payload = payload_b.decode("utf8")

        return packet
