import os
from unittest import mock

import numato_gpio
import pytest

from common import PORTS


@pytest.mark.parametrize("ports", PORTS)
def test_main(ports, mock_device, monkeypatch, capsys):

    with mock.patch.object(numato_gpio.discover, "__defaults__", (["/dev/ttyACMxx"],)):

        monkeypatch.setattr("serial.Serial.ports", ports)
        from numato_gpio.__main__ import main

        main()
        cap = capsys.readouterr()
        assert cap.out.startswith(f"Discovered devices: {os.linesep}dev: /dev/ttyACMxx")
        assert cap.err == ""


# @pytest.mark.parametrize("ports", PORTS)
# def test_error_duplicate_device(ports, mock_device, monkeypatch):
#     from numato_gpio.__main__ import main
#     device2 = deepcopy(mock_device)
#     monkeypatch.setattr("serial.Serial.ports", ports)
#     main()
