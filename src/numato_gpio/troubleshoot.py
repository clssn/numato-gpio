import serial
import sys
from pathlib import Path

def main():

    if len(sys.argv) != 2:
        print(f"\nUsage: {sys.argv[0]} DEVICE")
        print()
        print(f"  DEVICE  Device file, e.g. /dev/ttyACM0")
        exit(1)
    elif not Path(sys.argv[1]).exists():
        print(f"Path {sys.argv[1]} doesn't exist.")
        exit(1)
    elif not Path(sys.argv[1]).is_char_device():
        print(f"Path {sys.argv[1]} is not a character device.")
        exit(1)

    commands = [
        b'gpio notify off\r',
        b'id get\r',
        b'ver\r',
        b'gpio iomask ffffffff\r',
        b'gpio iomask 00000000\r',
        b'gpio readall\r',
    ]

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
