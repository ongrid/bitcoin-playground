from electrum_rpc_client import ElectrumRpcClient
from bitcoind_rpc_client import BitcoindRpcClient
from bitcoinutils.hdwallet import HDWallet
from bitcoinutils.setup import setup

MNEMONIC = "test test test test test test test test test test test junk"
BITCOIND_URL = "http://bitcoind:18443/"
ELECTRUMX_HOST = "electrumx"
ELECTRUMX_PORT = 50001
BITCOIND_USER = "btc"
BITCOIND_PASSWORD = "btc"
NETWORK = "regtest"
SUPPORTED_MIME_TYPES = ["text/html", "image/png", "image/svg", "image/webp", "text/javascript"]

setup(NETWORK)
hdw = HDWallet(mnemonic=MNEMONIC)
hdw.from_path("m/86'/0'/0'/0/0")
alice_priv_key = hdw.get_private_key()
alice_p2tr = alice_priv_key.get_public_key().get_taproot_address()
hdw.from_path("m/44'/0'/0'/0/0")
miner_priv_key = hdw.get_private_key()
miner_p2tr = miner_priv_key.get_public_key().get_taproot_address()

btc = BitcoindRpcClient(BITCOIND_URL, BITCOIND_USER, BITCOIND_PASSWORD)
ele = ElectrumRpcClient(ELECTRUMX_HOST, ELECTRUMX_PORT)
