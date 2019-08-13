import logging, serial, Sensor
from TUI import TUI

def main():
    logging.basicConfig(format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%H:%M:%S', level=logging.INFO)
    serial_ports = serial.tools.list_ports.comports()
    boards = []
    for port in serial_ports:
        if(port.vid == 1240 and port.pid == 10):
            boards.append(port.device)
    print("Select which device to use: " + str(boards))
    COM_port = input(">")
    sensor = Sensor.Sensor(COM_port)
    tui = TUI(sensor)
    tui.show()

if __name__ == "__main__":
    main()
