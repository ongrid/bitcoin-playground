import socket
from jsonrpcclient import request_json, parse_json, Ok, Error

class ElectrumRpcClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def call(self, method, *params):
        # Prepare JSON-RPC request payload
        message = request_json(method, *params)
        message += "\n"

        with socket.create_connection((self.host, self.port)) as sock:
            # Wrap the socket with SocketIO for line-oriented reading
            sock_file = socket.SocketIO(sock, "rwb")

            # Send the request
            sock_file.write(message.encode("utf-8"))
            sock_file.flush()

            # Read the response line
            response_line = sock_file.readline()
            if not response_line:
                raise Exception("No response from server")

            # Parse the response
            match parse_json(response_line):
                case Ok(result, id):
                    return result
                case Error(code, message, data, id):
                    raise Exception(message)
