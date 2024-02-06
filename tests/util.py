import json
import os
from typing import Any, Dict, Optional

from unittest.mock import AsyncMock, Mock, patch

def build_device(device_conf_name: str, device_state_name: str, energy_report: Optional[Dict[Any, Any]]=None):
    test_dir = os.path.join(os.path.dirname(__file__), "samples")
    with open(os.path.join(test_dir, device_conf_name), "r") as json_file:
        device_conf = json.load(json_file)

    with open(os.path.join(test_dir, device_state_name), "r") as json_file:
        device_state = json.load(json_file)

    with patch("pymelcloud.client.Client") as _client:
        _client.update_confs = AsyncMock()
        _client.device_confs.__iter__ = Mock(return_value=[device_conf].__iter__())
        _client.fetch_device_units = AsyncMock(return_value=[])
        _client.fetch_device_state = AsyncMock(return_value=device_state)
        _client.fetch_energy_report = AsyncMock(return_value=energy_report)
        client = _client

    return device_conf, client
