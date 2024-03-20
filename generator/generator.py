import requests
import json
from bitcoinutils.setup import setup
from bitcoinutils.hdwallet import HDWallet
from bitcoinutils.ripemd160 import ripemd160
from bitcoinutils.utils import to_satoshis
from bitcoinutils.script import Script
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput
from electrum_rpc_client import ElectrumRpcClient
from bitcoind_rpc_client import BitcoindRpcClient
from utils import get_script_hash
from pprint import pprint
from time import sleep
from config import NETWORK, ele, btc, alice_priv_key, alice_p2tr, miner_priv_key, miner_p2tr

FEE = to_satoshis(0.01)
MIN_BLOCKS = 100

btc.call("createwallet", "wallet")
blocks = btc.call("getblockcount").json()["result"]
if blocks < MIN_BLOCKS:
    btc.call("generatetoaddress", MIN_BLOCKS - blocks, miner_p2tr.to_string())


# generating blocks until first input appears
while True:
    unspent = ele.call(
        "blockchain.scripthash.listunspent",
        [get_script_hash(miner_p2tr.to_string(), network=NETWORK)],
    )
    if unspent:
        print(f"Miner has UTXO(s):{unspent}")
        break


# Send funds from miner's wallet to Alice using pay-to-taproot
# See https://github.com/karask/python-bitcoin-utils/blob/master/examples/send_to_p2tr_with_single_script.py

tr_script_p2pk = Script(
    [alice_priv_key.get_public_key().to_x_only_hex(), "OP_CHECKSIG"]
)
tx_in = TxInput(unspent[0]["tx_hash"], unspent[0]["tx_pos"])
amount_to_send = unspent[0]["value"] - FEE
tx_out = TxOutput(amount_to_send, alice_p2tr.to_script_pub_key())
tx = Transaction([tx_in], [tx_out], has_segwit=True)
print("Raw transaction:\n" + tx.serialize())
print("txid: " + tx.get_txid())
print("txwid: " + tx.get_wtxid())
sig = miner_priv_key.sign_taproot_input(
    tx, 0, [miner_p2tr.to_script_pub_key()], [unspent[0]["value"]]
)
tx.witnesses.append(TxWitnessInput([sig]))
ele.call("blockchain.transaction.broadcast", [tx.serialize()])
tx_appeared_in_unspent = False
while True:
    btc.call("generatetoaddress", 1, miner_p2tr.to_string())
    sleep(1)
    unspent = ele.call(
        "blockchain.scripthash.listunspent",
        [get_script_hash(alice_p2tr.to_string(), network=NETWORK)],
    )
    for utxo in unspent:
        if utxo["tx_hash"] == tx.get_txid():
            tx_appeared_in_unspent = True
    if tx_appeared_in_unspent:
        break

print(f"Alice's UTXO(s):")
pprint(unspent)
