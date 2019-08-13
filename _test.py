from enum import Enum

# import serial, io, time
# import Hub

# serial_ports = serial.tools.list_ports.comports()
# boards = []
# for port in serial_ports:
#     if(port.vid == 1240 and port.pid == 10):
#         boards.append(port.device)
# # print("Select which device to use: " + str(boards))

# s = serial.Serial()
# s.port = "COM4"
# s.baudrate = 57600
# s.bytesize = serial.EIGHTBITS
# s.parity = serial.PARITY_NONE
# s.stopbits = serial.STOPBITS_ONE
# s.timeout = 0.05 #seconds
# s.open()

# sio = io.TextIOWrapper(s, newline="\r\n")
# sio.write("mac pause\n")
# sio.flush() # it is buffering. required to get the data out *now*
# response = sio.readline()
# print(response)
# sio.write("radio get bw\n")
# sio.flush() # it is buffering. required to get the data out *now*
# response = sio.readline()
# print(response)


# # s.write(b'mac pause\r\n')
# # time.sleep(1)
# # while(s.in_waiting > 0):
# #     response = s.read(1)
# #     print(response)
# s.close()
class PType():
    DATA_UP = '000'
    ACK = '001'
    JOIN = '010'
    AUTOSET = '011'

a = PType.DATA_UP
print(a)