import time
from typing import Tuple
from aptos_sdk.account import Account
from aptos_sdk.async_client import FaucetClient, RestClient, ClientConfig
from aptos_sdk.transactions import EntryFunction, TransactionPayload, TransactionArgument, RawTransaction, SignedTransaction
from aptos_sdk.bcs import Serializer

class AptosSDKPlus(RestClient):
    def __init__(self, base_url, client_config: ClientConfig = ClientConfig()):
        super().__init__(base_url, client_config)

    async def transact(
            self,
            entry_function: EntryFunction,
            account_from: Account,
            max_gas_amount: int = 2000,
            gas_unit_price: int = 100,
            expiration_timestamps_secs: int = int(time.time()) + 600,
            wait: bool = True
        ) -> str | Tuple[bool, str, int]:
        # Get the chain ID for the transaction
        chain_id = await self.chain_id()
        
        # Get the sender's current sequence number
        account_data = await self.account(account_from.address())
        sequence_number = int(account_data["sequence_number"])
        
        # Create the raw transaction with all required fields
        raw_transaction = RawTransaction(
            sender=account_from.address(),                                    # Sender's address
            sequence_number=sequence_number,                           # Sequence number to prevent replay attacks
            payload=TransactionPayload(entry_function),                # The function to call
            max_gas_amount=max_gas_amount,                                       # Maximum gas units to use
            gas_unit_price=gas_unit_price,                                        # Price per gas unit in octas
            expiration_timestamps_secs=expiration_timestamps_secs,         # Expires in 10 minutes
            chain_id=chain_id,                                         # Chain ID to ensure correct network
        )
        
        # print("Transaction built successfully")
        # print(f"Sender: {raw_transaction.sender}")
        # print(f"Sequence Number: {raw_transaction.sequence_number}")
        # print(f"Max Gas Amount: {raw_transaction.max_gas_amount}")
        # print(f"Gas Unit Price: {raw_transaction.gas_unit_price}")
        # print(f"Expiration Timestamp: {time.ctime(raw_transaction.expiration_timestamps_secs)}")

        # 3. Sign the transaction
        # print("\n=== 3. Signing the transaction ===")
        
        # Sign the raw transaction with the sender's private key
        # This creates a cryptographic signature that proves the sender authorized this transaction
        authenticator = account_from.sign_transaction(raw_transaction)
        signed_transaction = SignedTransaction(raw_transaction, authenticator)
        
        # print("Transaction signed successfully")

        # 4. Submit the transaction
        # print("\n=== 4. Submitting the transaction ===")
        
        # Submit the signed transaction to the blockchain
        # This broadcasts the transaction to the network for processing
        tx_hash = await self.submit_bcs_transaction(signed_transaction)
        
        # print(f"Transaction submitted with hash: {tx_hash}")

        if wait:
            return await self.wait_tx(tx_hash)
        else:
            return tx_hash
    
    async def wait_tx(self, tx_hash: str) -> Tuple[bool, str, int]:
        await self.wait_for_transaction(tx_hash)
        transaction_details = await self.transaction_by_hash(tx_hash)
        success = transaction_details["success"]
        vm_status = transaction_details["vm_status"]
        gas_used = transaction_details["gas_used"]
        return bool(success), str(vm_status), int(gas_used)
        
        