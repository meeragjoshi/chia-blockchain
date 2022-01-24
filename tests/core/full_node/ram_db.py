from databases import Database
from typing import Tuple
from pathlib import Path

from chia.consensus.blockchain import Blockchain
from chia.consensus.constants import ConsensusConstants
from chia.full_node.block_store import BlockStore
from chia.full_node.coin_store import CoinStore
from chia.full_node.hint_store import HintStore
from chia.util.db_factory import create_database
from chia.util.db_wrapper import DBWrapper


async def create_ram_blockchain(consensus_constants: ConsensusConstants) -> Tuple[Database, Blockchain]:
    connection = create_database(":memory:")
    await connection.connect()
    db_wrapper = DBWrapper(connection)
    block_store = await BlockStore.create(db_wrapper)
    coin_store = await CoinStore.create(db_wrapper)
    hint_store = await HintStore.create(db_wrapper)
    blockchain = await Blockchain.create(coin_store, block_store, consensus_constants, hint_store, Path("."))
    return connection, blockchain
