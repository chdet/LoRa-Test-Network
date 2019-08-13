import serial
import io, time, logging

class NodeInterface:
    def __init__(self, COM_port):
        # COM_port is a string

        self.s = serial.Serial()
        self.s.port = COM_port
        self.s.baudrate = 57600
        self.s.bytesize = serial.EIGHTBITS
        self.s.parity = serial.PARITY_NONE
        self.s.stopbits = serial.STOPBITS_ONE
        self.s.timeout = 0.05 #seconds   The readline function hangs around for twice the timeout value, so timeout has to be set to a low
        self.s.open()
        self.sio = io.TextIOWrapper(io.BufferedRWPair(self.s,self.s), newline="\r\n")

    def close(self):
        self.s.close()

    def send(self, serial_cmnd):
        """ Sends a command to the serial device and return the immediate response

            Arguments:
                self.sio     -- TextIOWrapper object
                serial_cmnd  -- String object
        """
        self.sio.write(serial_cmnd+"\n")   # TextIOWrapper object converts the newline character to "\r\n", this is required by the device 
        self.sio.flush() # it is buffering. required to get the data out *now*
        response = self.sio.readline()
        response = response.rstrip()   # Trim the newline character
        if (response == "ok"):
            return True
        else:
            logging.debug("Board response:" + response) 
            return response

    def read_raw(self):
        return repr(self.sio.read(1000))
        # return self.sio.read(1000)


    def read_input_buffer(self):
        serial_inputs = []
        elem = self.sio.readline().rstrip()
        while(elem != ""):
            serial_inputs.append(elem)
            elem = self.sio.readline().rstrip()
        return serial_inputs

    def wait_for_serial(self, timeout = 10):
        tic = time.clock()
        while(self.s.in_waiting == 0 and (time.clock() - tic) < timeout):
            pass
        if(self.s.in_waiting > 0):
            return True
        else: 
            return False

    def listen(self, timeout = 15):
        if(self.send('radio rx 0') == True):
            if(self.wait_for_serial(timeout)):
                response = self.sio.readline()
                return response 
            else:
                return None
        else:
            return False

    def get_snr(self):
        snr = self.send('radio get snr')
        return snr

    def get_configuration(self):
        parameters = ['sf', 'cr', 'bw', 'pwr', 'wdt']
        values = {}
        for parameter in parameters:
            value = self.send('radio get ' + parameter)
            values[parameter] = value
        return values


    # def configure(self, param_cmds):
    #     # param_cmds is a list of commands used to configure the LoRaMote

    #     err = False
    #     for param_cmd in param_cmds:
    #         response = self.send(param_cmd)
    #         if(response != True):
    #             err = True
    #     if(err == False):
    #         return True
    #     else:
    #         return False

