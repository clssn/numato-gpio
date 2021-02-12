import os

import pytest
from numato_gpio import NumatoGpioError
from copy import deepcopy
from common import PORTS


@pytest.mark.parametrize("ports", PORTS)
def test_main(ports, mock_device, monkeypatch, capsys):
    from numato_gpio.__main__ import main

    monkeypatch.setattr("serial.Serial.ports", ports)
    main()
    cap = capsys.readouterr()
    assert cap.out.startswith(
        f"Discovered devices: {os.linesep}dev: /dev/ttyACM0"
    )
    assert cap.err == ""


# @pytest.mark.parametrize("ports", PORTS)
# def test_error_duplicate_device(ports, mock_device, monkeypatch):
#     from numato_gpio.__main__ import main
#     device2 = deepcopy(mock_device)
#     monkeypatch.setattr("serial.Serial.ports", ports)
#     main()
