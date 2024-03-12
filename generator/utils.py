from pycoin.symbols.btc import network as btc_mainnet
from pycoin.symbols.xtn import network as btc_testnet
from pycoin.symbols.xrt import network as btc_regtest
import hashlib

def get_script_hash(addr, network="mainnet"):
    if network == "mainnet":
        pycsymbol = btc_mainnet
    elif network == "testnet":
        pycsymbol = btc_testnet
    elif network == "regtest":
        pycsymbol = btc_regtest
    script = pycsymbol.parse.address(addr).script()
    return hashlib.sha256(script).digest()[::-1].hex()
