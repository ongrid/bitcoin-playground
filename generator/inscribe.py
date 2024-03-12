from btclib.script.script_pub_key import ScriptPubKey
from utils import get_script_hash, FeeCalculator
from bitcoinutils.setup import setup
from bitcoinutils.hdwallet import HDWallet
from bitcoinutils.utils import to_satoshis, ControlBlock
from bitcoinutils.script import Script
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput
from electrum_rpc_client import ElectrumRpcClient
from bitcoind_rpc_client import BitcoindRpcClient
from pprint import pprint
from time import sleep

MNEMONIC = "test test test test test test test test test test test junk"
BITCOIND_URL = "http://bitcoind:18443/"
ELECTRUMX_HOST = "electrumx"
ELECTRUMX_PORT = 50001
MIN_BLOCKS = 100
BITCOIND_USER = "btc"
BITCOIND_PASSWORD = "btc"
NETWORK = "regtest"

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

unspent = ele.call(
    "blockchain.scripthash.listunspent",
    [get_script_hash(alice_p2tr.to_string(), network=NETWORK)],
)
print(f"Alice's UTXO(s):")
pprint(unspent)

vin = TxInput(unspent[0]["tx_hash"], unspent[0]["tx_pos"])

sat_per_vbyte = 2.0
payload = "deadbeef" * 20
print(payload)
print(len(payload))
taproot_script_p2pk = Script(
    [
        alice_priv_key.get_public_key().to_x_only_hex(),
        "OP_CHECKSIG",
        "OP_0",
        "OP_IF",
        "ord".encode("utf-8").hex(),
        "01",
        "text/plain;charset=utf-8".encode("utf-8").hex(),
        "OP_0",
        payload,
        "OP_ENDIF",
    ]
)

taproot_script_address = alice_priv_key.get_public_key().get_taproot_address(
    [[taproot_script_p2pk]]
)

fee_calculator = FeeCalculator(sat_per_vbyte=43.3)
reveal_vsize_bytes = fee_calculator.predict_vsize_bytes(taproot_script_p2pk)
reveal_fee_satoshis = fee_calculator.predict_fee(reveal_vsize_bytes)

inscription_utxo_value = 1250
commit_value = reveal_fee_satoshis + inscription_utxo_value
commit_fee = 10_000  # need to calculate
change_value = unspent[0]["value"] - commit_value - commit_fee

vout_commit = TxOutput(commit_value, taproot_script_address.to_script_pub_key())
vout_change = TxOutput(change_value, alice_p2tr.to_script_pub_key())
commit_tx = Transaction([vin], [vout_commit, vout_change], has_segwit=True)
sig = alice_priv_key.sign_taproot_input(
    commit_tx, 0, [alice_p2tr.to_script_pub_key()], [unspent[0]["value"]]
)
commit_tx.witnesses.append(TxWitnessInput([sig]))
print("Commit Tx:", commit_tx.get_txid())
res = ele.call("blockchain.transaction.broadcast", [commit_tx.serialize()])

vin = TxInput(commit_tx.get_txid(), 0)

# todo: refactor
vout = TxOutput(
    inscription_utxo_value,
    Script.from_raw(ScriptPubKey.from_address(alice_p2tr.to_string()).script.hex()),
)
rev_tx = Transaction([vin], [vout], has_segwit=True)
sig = alice_priv_key.sign_taproot_input(
    rev_tx,
    0,
    [taproot_script_address.to_script_pub_key()],
    [commit_tx.outputs[0].amount],
    script_path=True,
    tapleaf_script=taproot_script_p2pk,
    tapleaf_scripts=[taproot_script_p2pk],
    tweak=False,
)
control_block = ControlBlock(alice_priv_key.get_public_key())
rev_tx.witnesses.append(
    TxWitnessInput([sig, taproot_script_p2pk.to_hex(), control_block.to_hex()])
)
print("Reveal Tx:", rev_tx.get_txid())
print(rev_tx.serialize())
res = ele.call("blockchain.transaction.broadcast", [rev_tx.serialize()])

# wait reveal tx mined and reveal UTXO become spendable by Alice
while True:
    unspent = ele.call(
        "blockchain.scripthash.listunspent",
        [get_script_hash(alice_p2tr.to_string(), network=NETWORK)],
    )
    for i in unspent:
        if i['tx_hash'] == rev_tx.get_txid():
            print(f"Reveal Tx {rev_tx.get_txid()} mined successfully.")
            break
    else:
        btc.call("generatetoaddress", 1, miner_p2tr.to_string())
        sleep(1)
    break