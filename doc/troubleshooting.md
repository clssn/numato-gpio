Troubleshoting
==============

In case your device can't be discovered, please try to follow below steps to
collect information about the problem before opening an issue.

# Collect some information

0. Connnect your device

1. Power LED (if available on your device) is on

2. `dmesg` (Kernel log) shows that the device is detected and assigned a device
   file like so:

        [719716.044331] usb 1-9: new full-speed USB device number 22 using xhci_hcd
        [719716.194928] usb 1-9: New USB device found, idVendor=2a19, idProduct=0802, bcdDevice= 1.00
        [719716.194930] usb 1-9: New USB device strings: Mfr=1, Product=2, SerialNumber=0
        [719716.194931] usb 1-9: Product: CDC RS-232 Emulation Demo
        [719716.194931] usb 1-9: Manufacturer: Microchip Technology Inc.
        [719716.215038] cdc_acm 1-9:1.0: ttyACM0: USB ACM device
        [719716.215317] usbcore: registered new interface driver cdc_acm
        [719716.215318] cdc_acm: USB Abstract Control Model driver for USB modems and ISDN adapters

    Note that the device could have a different number. If it doesn't start
    with `ttyACM` this might be interesting, since it's different to my setup.

3. Confirm the device file with `ls -l /dev/ttyACM0` and should get

        crw-rw---- 1 root dialout 166, 0 Jan 16 16:55 /dev/ttyACM0

    Make sure it has rw permissions for user and group as shown above.

4. In case you are using a non-root user (which is recommended) make sure that
   your user is member of the `dialout` group. You can check this with `id
   -Gn`. If this is not the case your user has no permissions to use the
   device. Add your user (e.g. `pi` on a Raspberry PI) to the `dialout` group
   like: `sudo adduser pi dialout`

5. Install GNU Screen (on Ubuntu `sudo apt screen` ) and connect it to your
   device with `screen /dev/ttyACM0`. Now try to reproduce the following
   command/anwser sequence:

        id get
        00000000
        >ver
        00000009
        >gpio readall
        FFFFFFFF
        >gpio notify get
        gpio notify disabled
        >

    Kill the screen session with `Ctrl+a k`.

6. Install the latest development version of `numato-gpio` Python package as
   explained in the [README](../README.md#Install) and run it like `python3 -m
   numato_gpio`. The output should be like:

        Discovered devices:
        dev: /dev/ttyACM0 | id: 2 | ver: 9 | ports: 32 | iodir: 0xffffffff | iomask: 0x00000000 | state: 0x00000000

7. If 6. wasn't successful, run `python3 -m numato_gpio.troubleshoot`. Make
   sure to include the output in your issue.

# Contact me

1. Look at the [issues](https://github.com/clssn/numato-gpio/issues), whether your problem is already reported/discussed.
2. If not, please open a [new issue](https://github.com/clssn/numato-gpio/issues/new/choose).

Please describe your problem as precise as possible, in particular:

    - Your Numato device
    - Your OS/platform
    - Python version
    - Release version of numato-gpio or branch/commit if applicable
    - Any deviation from the above troubleshooting instructions, or better the whole terminal output.
    - Anything else you already tried

# Be patient

Please be aware that the time I can spend for this software is limited.
Nevertheless, I am motivated to constantly increase the quality of this Python
module and to maintain it in a professional way.
