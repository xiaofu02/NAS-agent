# utils/formatters.py

import json


def print_generic_json(result: dict):
    print(json.dumps(result, indent=2, ensure_ascii=False))