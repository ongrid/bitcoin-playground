# Bitcoin Playground

This repository hosts the setup for a comprehensive Bitcoin playground environment, aimed at enabling users to explore and interact with Bitcoin in a sandboxed, isolated setting. The environment consists of a `bitcoind` BTC node running in regtest mode, an `electrumx` indexer to facilitate transaction indexing, and a custom script designed to generate blocks to a well-known address, allowing users the flexibility to spend in a contained ecosystem.

## Components

- `bitcoind` in regtest mode: A private Bitcoin network for development that allows for block generation on demand.
- `electrumx` indexer: Indexes blockchain transactions, enabling interaction with the blockchain data.
- `generator` custom block generation script: Automates the creation of blocks to a predetermined addresses, streamlining the process of obtaining spendable satoshis

## Setup Instructions

- Install Docker and Docker compose
- Build and run the setup

```sh
docker compose build
docker compose up
```

## Usage

Upon setup, the script in `generator` container will create two accounts and generate approximately 100 blocks to the Miner's address and transfer a certain amount of bitcoins to the address of Alice.

You can import the wallets of both parties using their seed phrases into your software to access these funds.

Connections to bitcoind and electrum can be established using the following credentials:

Additionally, the repository contains a simple client wrapper for sending RPC commands to both daemons

## Methods and APIs

Documentation on Electrum and Bitcoind, including their methods, can be found here:

* Spesmilo's ElectrumX [documentation](https://electrumx-spesmilo.readthedocs.io/en/latest/) and [repository](https://github.com/spesmilo/electrumx)
* Bitcoind aka Bitcoin Core [documentation](https://developer.bitcoin.org/reference/rpc/index.html), [repo](https://github.com/bitcoin/bitcoin), Chiang Mai's [docker](https://hub.docker.com/r/lncm/bitcoind)

Happy experimenting!
