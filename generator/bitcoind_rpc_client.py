import json
import requests

JSONRPC_PAYLOAD_TEMPLATE = {
    "method": "",
    "params": [],
    "jsonrpc": "1.0",
    "id": 0,
}

HTTP_HEADERS = {'content-type': 'application/json'}


class BitcoindRpcClient:
    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password

    def call(self, method, *params):
        payload = JSONRPC_PAYLOAD_TEMPLATE.copy()
        payload["method"] = method
        payload["params"] = list(params)
        return requests.post(self.url, data=json.dumps(payload), headers=HTTP_HEADERS, auth=(self.user, self.password))
