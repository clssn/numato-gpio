import serial
import sys
import math
from pathlib import Path

def main():

    if len(sys.argv) != 3:
        print(f"\nUsage: {sys.argv[0]} DEVICE PORTS")
        print()
        print(f"  DEVICE  Device file, e.g. /dev/ttyACM0")
        print(f"  PORTS   Number of IO ports of your Device")
        exit(1)
    elif not Path(sys.argv[1]).exists():
        print(f"Path {sys.argv[1]} doesn't exist.")
        exit(1)
    elif not Path(sys.argv[1]).is_char_device():
        print(f"Path {sys.argv[1]} is not a character device.")
        exit(1)

    try:
        ports = int(sys.argv[2])
        if ports not in [2**x for x in range(3,8)]:
            raise ValueError()
    except(ValueError):
        print("Number of IO ports needs to be 8, 16, 32, 64 or 128")
        exit(1)

    commands = [
        b'id get\r',
        b'ver\r',
        'gpio iomask {:0{dgts}x}\r'.format(2**ports - 1, dgts=ports//4).encode(),
        'gpio iomask {:0{dgts}x}\r'.format(0, dgts=ports//4).encode(),
        b'gpio readall\r',
    ]

    if ports != 8:
        commands.append(b'gpio notify off\r')


    device = sys.argv[1]
    read_max = 1000

    print(f"Testing device {device} with pyserial=={serial.__version__}\n")
    for command in commands:
        ser = serial.Serial(device, 19200, timeout=0.1)
        print(f"writing to {device}: {command}")
        ser.write(command)
        buf = ser.read(read_max)
        print(f"response ({len(buf)} byte):\n{buf}")
        print(" ".join(hex(c) for c in buf))
        print("--")
        ser.close()

if __name__ == "__main__":
    main()
