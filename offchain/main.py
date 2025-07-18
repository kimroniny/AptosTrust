import asyncio
from typing import List, Tuple
from aptos_sdk.account import Account
from aptos_sdk.async_client import FaucetClient, RestClient
from aptos_sdk.transactions import EntryFunction, TransactionPayload, TransactionArgument, RawTransaction
from aptos_sdk.bcs import Serializer
from aptos_sdk import ed25519
from aptos_sdk.account_address import AccountAddress
import time
from sdk.sdk import AptosSDKPlus
 
# Network configuration
NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"
FAUCET_URL = "https://faucet.devnet.aptoslabs.com"

MODULE = "0x9351b6102cc8a05e5b05fedd1f3f3e44f2f760518aa4d1334914e014d165210a::AptosTrust"

parachain_height = int(time.time()*1000)

async def registParachain(sdk: AptosSDKPlus, account_from: Account, chainId: int):
    # Create the entry function payload
    # This specifies which function to call and with what arguments
    entry_function = EntryFunction.natural(
        MODULE,  # Module address and name
        "registParaChain",            # Function name
        [],                    # Type arguments (empty for this function)
        [
            TransactionArgument(chainId, Serializer.u64),                      # parachain chainId
        ],
    )
    
    success, vm_status, gas_used = await sdk.transact(
        entry_function=entry_function,
        account_from=account_from,
        wait=True
    )
    
    # print(f"Transaction(registParachain:{chainId}) completed with status: {'SUCCESS' if success else 'FAILURE'}")
    print(f"--- VM Status: {vm_status}")
    print(f"--- Gas used: {gas_used}")

    result = await sdk.view_bcs_payload(
        module=MODULE,
        function="getParachain",
        ty_args=[],
        args=[
            TransactionArgument(chainId, Serializer.u64),
        ]
    )
    assert result[0], ""

    result = await sdk.view_bcs_payload(
        module=MODULE,
        function="getParachainCount",
        ty_args=[],
        args=[]
    )
    parachain_count = int(result[0])
    print(f"regist parachain {chainId} ok! Number of parachains: {parachain_count}")
    print(f"--- VM Status: {vm_status}")
    print(f"--- Gas used: {gas_used}")

async def registAllParachains(sdk: AptosSDKPlus, account_from: Account, chainIds: List[int]):
    print(f"*********************************************************")
    print(f"register all parachains to Aptos(Hub)")
    for chainId in chainIds:
        await registParachain(sdk=sdk, account_from=account_from, chainId=chainId)
    print(f"*********************************************************")

async def sendHeaderToRelaychainBy1001(sdk: AptosSDKPlus, account_from: Account) -> Tuple[int, int]:
    # collectHeader
    # public entry fun collectHeader(operator: &signer, chainId: u64, height: u64, root: vector<u8>, hcr: vector<u8>, sequences: vector<u64>) acquires AllHeaders,VotesByHeight,HCRByHeight
    chainId = 1001
    global parachain_height
    parachain_height += 1
    height = parachain_height
    root = [1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8]
    hcr = [1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8]
    sequences = []
    entry_function = EntryFunction.natural(
        MODULE,  # Module address and name
        "collectHeader",            # Function name
        [],                    # Type arguments (empty for this function)
        [
            TransactionArgument(chainId, Serializer.u64), # parachain chainId
            TransactionArgument(height, Serializer.u64), # parachain header height
            TransactionArgument(root, Serializer.sequence_serializer(Serializer.u8)), # parachain header root
            TransactionArgument(hcr, Serializer.sequence_serializer(Serializer.u8)), # parachain hcr
            TransactionArgument(sequences, Serializer.sequence_serializer(Serializer.u64)), # parachain sequences of relay chain height
        ],
    )
    success, vm_status, gas_used = await sdk.transact(
        entry_function=entry_function,
        account_from=account_from,
        wait=True
    )
    # print(f"Transaction(sendHeaderToRelaychainBy1001) completed with status: {'SUCCESS' if success else 'FAILURE'}")
    
    result = await sdk.view_bcs_payload(
        module=MODULE,
        function="getHeader",
        ty_args=[],
        args=[
            TransactionArgument(chainId, Serializer.u64), # parachain chainId
            TransactionArgument(height, Serializer.u64), # parachain header height
        ]
    )
    relayHeight = int(result[0])
    print(f"store parachain({chainId}) header({height}) on Aptos(Hub): {result}")
    print(f"--- VM Status: {vm_status}")
    print(f"--- Gas used: {gas_used}")
    return height, relayHeight

async def collectHeaderFromEachParachain(
        sdk: AptosSDKPlus, 
        account_from: Account, 
        chainId: int, 
        height: int, 
        sequences: List[int]
    ):
    root = [1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8]
    hcr = [1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8]
    # sequences = []
    entry_function = EntryFunction.natural(
        MODULE,  # Module address and name
        "collectHeader",            # Function name
        [],                    # Type arguments (empty for this function)
        [
            TransactionArgument(chainId, Serializer.u64), # parachain chainId
            TransactionArgument(height, Serializer.u64), # parachain header height
            TransactionArgument(root, Serializer.sequence_serializer(Serializer.u8)), # parachain header root
            TransactionArgument(hcr, Serializer.sequence_serializer(Serializer.u8)), # parachain hcr
            TransactionArgument(sequences, Serializer.sequence_serializer(Serializer.u64)), # parachain sequences of relay chain height
        ],
    )
    success, vm_status, gas_used = await sdk.transact(
        entry_function=entry_function,
        account_from=account_from,
        wait=True
    )
    # print(f"Transaction(collectHeaderFromEachParachain) completed with status: {'SUCCESS' if success else 'FAILURE'}")
    
    result = await sdk.view_bcs_payload(
        module=MODULE,
        function="getHeader",
        ty_args=[],
        args=[
            TransactionArgument(chainId, Serializer.u64), # parachain chainId
            TransactionArgument(height, Serializer.u64), # parachain header height
        ]
    )
    print(f"")
    print(f"*********************************************************")
    print(f"Aptos(Hub) collects parachain header(chainId={chainId}, height={height}), included into block({int(result[0])})")
    print(f"--- VM Status: {vm_status}")
    print(f"--- Gas used: {gas_used}")

async def queryVote(sdk: AptosSDKPlus, account_from: Account, para_chain_id: int, para_chain_height: int, relay_height: int):
    result = await sdk.view_bcs_payload(
        module=MODULE,
        function="getRelayHeaderVotes",
        ty_args=[],
        args=[
            TransactionArgument(relay_height, Serializer.u64), # parachain chainId
        ]
    )
    votes, maxvotes = int(result[0]), int(result[1])
    print(f">>> check votes of parachain(chainId={para_chain_id}) header(height={parachain_height}): {votes}/{maxvotes}")
    print(f"*********************************************************")

async def collectHeadersFromParachains(
        sdk: AptosSDKPlus, 
        account_from: Account, 
        para_chain_id: int, 
        para_chain_height: int, 
        relay_height: int, 
        chainIds: List[int]
    ):
    global parachain_height
    parachain_height += 1
    await queryVote(sdk, account_from, para_chain_id, para_chain_height, relay_height)
    for chainId in chainIds:
        await collectHeaderFromEachParachain(sdk, account_from, chainId, parachain_height, sequences=[relay_height])
        await queryVote(sdk, account_from, para_chain_id, para_chain_height, relay_height)
    pass

async def evaluate(sdk: AptosSDKPlus, account_from: Account):
    # # regist 6 parachains [1001,1002,1003,1004,1005,1006]
    chainIds = [1001,1002,1003,1004,1005,1006]
    await registAllParachains(sdk, account_from, chainIds)
    
    # parachain 1001 sends header to relay chain
    para_chain_height, relay_height = await sendHeaderToRelaychainBy1001(sdk, account_from)

    input()

    # # relay chain sends header to six parachains
    # # # wait a moment to mimic the parachain consensus process

    # six parachain sends header to relay chain
    await collectHeadersFromParachains(
        sdk, 
        account_from, 
        para_chain_id=1001,
        para_chain_height=para_chain_height,
        relay_height=relay_height,
        chainIds=chainIds
    )
    
    pass

def load_key(key: str) -> Account:
    private_key = ed25519.PrivateKey.from_str(key, strict=False)
    account_address = AccountAddress.from_key(private_key.public_key())
    return Account(account_address, private_key)

async def main():
    # Initialize the clients
    sdk = AptosSDKPlus(NODE_URL)
    
    print("Connected to Aptos devnet")
    
    # More code will go here
    # Generate two accounts
    with open('./prepare_account/testkey/Alice', 'r') as f:
        account_alice = load_key(f.read())
    with open('./prepare_account/testkey/Bob', 'r') as f:
        account_bob = load_key(f.read())

    # evaluate
    await evaluate(sdk, account_alice)
    
 
if __name__ == "__main__":
    asyncio.run(main())