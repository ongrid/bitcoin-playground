import argparse
import mimetypes
import json
import sys
from btclib.script.script_pub_key import ScriptPubKey
from utils import get_script_hash, FeeCalculator
from bitcoinutils.utils import to_satoshis, ControlBlock
from bitcoinutils.script import Script
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput
from pprint import pprint
from time import sleep
import random
from config import NETWORK, ele, btc, alice_priv_key, alice_p2tr, miner_p2tr, SUPPORTED_MIME_TYPES


def main(filename):
    # Guess the MIME type of the file
    mime_type = mimetypes.guess_type(filename)[0]
    if mime_type not in SUPPORTED_MIME_TYPES:
        sys.exit(f'Error: Unsupported MIME type {mime_type}')
    if mime_type == "text/html":
        mime_type += ";charset=utf-8"

    print(f"Inscribing {filename} (MIME: {mime_type})")

    with open(filename, "rb") as file:
        content = file.read().hex()

    data = {
        'content': content,
        'type': mime_type,
        'script': None,
        'script_address': None
    }

    taproot_script_p2pk = Script(
        [
            alice_priv_key.get_public_key().to_x_only_hex(),
            "OP_CHECKSIG",
            "OP_0",
            "OP_IF",
            "ord".encode("utf-8").hex(),
            "01",
            mime_type.encode("utf-8").hex(),
            "OP_0",
            content,
            "OP_ENDIF",
        ]
    )

    data["script"] = taproot_script_p2pk.to_hex()
    with open(f'{filename}.json', 'w') as file:
        json.dump(data, file, indent=2)

    taproot_script_address = alice_priv_key.get_public_key().get_taproot_address(
        [[taproot_script_p2pk]]
    )

    data["script_address"] = taproot_script_address.to_string()
    # Write the JSON data to a file
    with open(f'{filename}.json', 'w') as file:
        json.dump(data, file, indent=2)

    fee_calculator = FeeCalculator(sat_per_vbyte=43.3)
    reveal_vsize_bytes = fee_calculator.predict_vsize_bytes(taproot_script_p2pk)
    reveal_fee_satoshis = fee_calculator.predict_fee(reveal_vsize_bytes)

    inscription_utxo_value = 1250
    commit_value = reveal_fee_satoshis + inscription_utxo_value
    commit_fee = 10_000  # need to calculate

    # find spendable UTXO that can pay both commit and reveal (the simplest case)
    # Generate (mine) if no UTXO available
    spendable_utxo = None
    while True:
        unspent = ele.call(
            "blockchain.scripthash.listunspent",
            [get_script_hash(alice_p2tr.to_string(), network=NETWORK)],
        )
        for i in unspent:
            if i['value'] > commit_value + commit_fee:
                spendable_utxo = i
                break
        else:
            print("No UTXO that we can use. Mining new satoshis.")
            btc.call("generatetoaddress", 1, alice_p2tr.to_string())
            # add new blocks to avoid errors like
            # bad-txns-premature-spend-of-coinbase, tried to spend coinbase at depth 5
            btc.call("generatetoaddress", 100, miner_p2tr.to_string())
            continue
        print(f"Found UTXO to spend {spendable_utxo}")
        break

    vin = TxInput(spendable_utxo["tx_hash"], spendable_utxo["tx_pos"])
    change_value = spendable_utxo["value"] - commit_value - commit_fee

    vout_commit = TxOutput(commit_value, taproot_script_address.to_script_pub_key())
    vout_change = TxOutput(change_value, alice_p2tr.to_script_pub_key())
    commit_tx = Transaction([vin], [vout_commit, vout_change], has_segwit=True)
    sig = alice_priv_key.sign_taproot_input(
        commit_tx, 0, [alice_p2tr.to_script_pub_key()], [spendable_utxo["value"]]
    )
    commit_tx.witnesses.append(TxWitnessInput([sig]))
    data["commit_tx"] = commit_tx.serialize()
    data["commit_txid"] = commit_tx.get_txid()
    with open(f'{filename}.json', 'w') as file:
        json.dump(data, file, indent=2)
    

    print("Commit Tx:", commit_tx.get_txid())

    res = ele.call("blockchain.transaction.broadcast", [commit_tx.serialize()])

    vin = TxInput(commit_tx.get_txid(), 0)

    vout = TxOutput(
        inscription_utxo_value,
        alice_p2tr.to_script_pub_key()
    )
    rev_tx = Transaction([vin], [vout], has_segwit=True)
    sig = alice_priv_key.sign_taproot_input(
        rev_tx,
        0,
        [taproot_script_address.to_script_pub_key()],
        [commit_tx.outputs[0].amount],
        script_path=True,
        tapleaf_script=taproot_script_p2pk,
        tweak=False,
    )
    control_block = ControlBlock(alice_priv_key.get_public_key(), is_odd=taproot_script_address.is_odd())
    rev_tx.witnesses.append(
        TxWitnessInput([sig, taproot_script_p2pk.to_hex(), control_block.to_hex()])
    )
    data["reveal_tx"] = rev_tx.serialize()
    data["reveal_txid"] = rev_tx.get_txid()
    with open(f'{filename}.json', 'w') as file:
        json.dump(data, file, indent=2)
    print("Reveal Tx:", rev_tx.get_txid())
    print(rev_tx.serialize())
    print(f"Script Len {len(taproot_script_p2pk.to_hex())/2} bytes")
    print(f"Tx Len {len(rev_tx.serialize())/2} bytes")
    res = btc.call("sendrawtransaction", rev_tx.serialize())
    print("Reveal Tx broadcasted:", res.json()['result'])
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
            continue
        break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Inscribe file')
    parser.add_argument('filename', help='The name of the file to inscribe')
    args = parser.parse_args()
    main(args.filename)
