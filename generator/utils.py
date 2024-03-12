from pycoin.symbols.btc import network as btc_mainnet
from pycoin.symbols.xtn import network as btc_testnet
from pycoin.symbols.xrt import network as btc_regtest
import hashlib
from bitcoinutils.script import Script


def get_script_hash(addr, network="mainnet"):
    if network == "mainnet":
        pycsymbol = btc_mainnet
    elif network == "testnet":
        pycsymbol = btc_testnet
    elif network == "regtest":
        pycsymbol = btc_regtest
    script = pycsymbol.parse.address(addr).script()
    return hashlib.sha256(script).digest()[::-1].hex()


class FeeCalculator:
    def __init__(self, sat_per_vbyte: float):
        self.sat_per_vbyte = sat_per_vbyte

    def predict_vsize_bytes(self, payload_script: Script):
        legacy_part_len = 96
        witness_len = 0
        witness_len += 1  # WITNESS STACK LENGTH PER EACH WITNESS
        witness_len += 64  # Schnorr Signature
        witness_len += len(payload_script.to_bytes())  # Variable part of inscriptions
        witness_len += 33  # Control block
        vsize = legacy_part_len + witness_len / 4
        return vsize

    def predict_fee(self, vsize_bytes):
        return int(self.sat_per_vbyte * vsize_bytes)
