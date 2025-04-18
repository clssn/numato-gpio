"""Specify fixed properties of supported Numato devices."""

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class DeviceSpec:
    """Base class for all device specifiers."""

    name: str
    url: str
    ports: int
    supports_notification: bool
    adc_resolution_bits: int
    adc_port_digits: int
    adc_ports: dict[int, str]


class DeviceType(Enum):
    """Specifiers for the supported Numato devices."""

    USB_GPIO_8 = DeviceSpec(
        name="8 Channel USB GPIO Module With Analog Inputs",
        url="https://numato.com/docs/8-channel-usb-gpio-module-with-analog-inputs",
        ports=8,
        supports_notification=False,
        adc_resolution_bits=10,
        adc_port_digits=1,
        adc_ports={
            0: "ADC0",
            1: "ADC1",
            2: "ADC2",
            3: "ADC3",
            6: "ADC4",
            7: "ADC5",
        },
    )
    USB_GPIO_16 = DeviceSpec(
        name="16 Channel USB GPIO Module With Analog Inputs",
        url="https://numato.com/docs/16-channel-usb-gpio-module-with-analog-inputs",
        ports=16,
        supports_notification=True,
        adc_resolution_bits=10,
        adc_port_digits=1,
        adc_ports={
            0: "ADC0",
            1: "ADC1",
            2: "ADC2",
            3: "ADC3",
            4: "ADC4",
            5: "ADC5",
            6: "ADC6",
        },
    )

    USB_GPIO_32 = DeviceSpec(
        name="32 Channel USB GPIO Module With Analog Inputs",
        url="https://numato.com/docs/32-channel-usb-gpio-module-with-analog-inputs",
        ports=32,
        supports_notification=False,
        adc_resolution_bits=10,
        adc_port_digits=1,
        adc_ports={
            1: "ADC1",
            2: "ADC2",
            3: "ADC3",
            4: "ADC4",
            5: "ADC5",
            6: "ADC6",
            7: "ADC7",
        },
    )
    USB_GPIO_64 = DeviceSpec(
        name="64 Channel USB GPIO Module With Analog Inputs",
        url="https://numato.com/docs/64-channel-usb-gpio-module-analog-inputs",
        ports=64,
        supports_notification=False,
        adc_resolution_bits=10,
        adc_port_digits=1,
        adc_ports={
            0: "ADC0",
            1: "ADC1",
            2: "ADC2",
            3: "ADC3",
            4: "ADC4",
            5: "ADC5",
            6: "ADC6",
            7: "ADC7",
            8: "ADC8",
            9: "ADC9",
            10: "ADC10",
            11: "ADC11",
            12: "ADC12",
            13: "ADC13",
            14: "ADC14",
            15: "ADC15",
            16: "ADC16",
            17: "ADC17",
            18: "ADC18",
            19: "ADC19",
            20: "ADC20",
            21: "ADC21",
            22: "ADC22",
            23: "ADC23",
            24: "ADC24",
            25: "ADC25",
            26: "ADC26",
            27: "ADC27",
            28: "ADC28",
            29: "ADC29",
            30: "ADC30",
            31: "ADC31",
        },
    )
    USB_GPIO_128 = DeviceSpec(
        name="128 Channel USB GPIO Module With Analog Inputs",
        url="https://numato.com/docs/128-channel-usb-gpio-module-with-analog-inputs",
        ports=128,
        supports_notification=False,
        adc_resolution_bits=10,
        adc_port_digits=1,
        adc_ports={
            0: "ADC0",
            1: "ADC1",
            2: "ADC2",
            3: "ADC3",
            4: "ADC4",
            5: "ADC5",
            6: "ADC6",
            7: "ADC7",
            8: "ADC8",
            9: "ADC9",
            10: "ADC10",
            11: "ADC11",
            12: "ADC12",
            13: "ADC13",
            14: "ADC14",
            15: "ADC15",
            16: "ADC16",
            17: "ADC17",
            18: "ADC18",
            19: "ADC19",
            20: "ADC20",
            21: "ADC21",
            22: "ADC22",
            23: "ADC23",
            24: "ADC24",
            25: "ADC25",
            26: "ADC26",
            27: "ADC27",
            28: "ADC28",
            29: "ADC29",
            30: "ADC30",
            31: "ADC31",
        },
    )


def spec_from_number_of_ports(num_ports: int) -> DeviceSpec:
    """Return device specification by the number of ports."""
    return {device_type.value.ports: device_type.value for device_type in DeviceType}[
        num_ports
    ]
