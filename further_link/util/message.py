import json
from typing import Dict


class BadMessage(Exception):
    pass


def create_message(msg_type, msg_data=None, msg_process=""):
    return json.dumps({"type": msg_type, "data": msg_data, "process": msg_process})


def append_to_message(message_str: str, dict_to_append: Dict) -> str:
    message_dict = json.loads(message_str)
    message_dict.update(dict_to_append)
    return json.dumps(message_dict)


def parse_message(message):
    try:
        msg = json.loads(message)
    except json.decoder.JSONDecodeError:
        raise BadMessage("Invalid JSON") from None

    msg_type = msg.get("type")
    msg_data = msg.get("data")
    msg_process = msg.get("process")

    msg_type = msg_type if isinstance(msg_type, str) else ""
    msg_data = msg_data if isinstance(msg_data, dict) else {}
    msg_process = msg_process if isinstance(msg_process, str) else ""

    return msg_type, msg_data, msg_process
