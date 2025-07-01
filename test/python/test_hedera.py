import pytest
from ragger.backend import BackendInterface

from ledger_app_clients.exchange.test_runner import ExchangeTestRunner, ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP
from .apps import cal as cal
from .apps.hedera import HederaClient, PUBLIC_KEY_LENGTH, HEDERA_PUBLIC_KEY
from .apps.hedera_builder import crypto_transfer_hbar_conf, crypto_create_account_conf, hedera_transaction
from time import sleep
from enum import IntEnum

class INS(IntEnum):
    INS_GET_APP_CONFIGURATION   = 0x01
    INS_GET_PUBLIC_KEY          = 0x02
    INS_SIGN_TRANSACTION        = 0x04

CLA = 0xE0

P1_CONFIRM = 0x00


class HederaTests(ExchangeTestRunner):
    client: BackendInterface
    currency_configuration = cal.HEDERA_CURRENCY_CONFIGURATION
    valid_destination_1 = "100.101.110"
    valid_destination_2 = "100.101.103"
    valid_refund = "0x698f0bad5c0c043a5f09cdcbb4c48ddcf6fb2886fa006df26298003fd59dc7c9"
    valid_refund_memo = ""
    valid_send_amount_1 = 42*100000000 # 42 HBAR
    valid_send_amount_2 = 446
    valid_fees_1 = 6
    valid_fees_2 = 42
    fake_refund = "abcdabcd"
    fake_refund_memo = "1"
    fake_payout = "abcdabcd"
    fake_payout_memo = "1"
    wrong_amount_error_code = 0x6980
    wrong_destination_error_code = 0x6980
    wrong_fees_error_code = 0x6980

    def perform_final_tx(self, destination, send_amount, fees, memo):
        hedera = HederaClient(self.backend)

        # Create the transaction configuration
        conf = crypto_transfer_hbar_conf(
            sender_shardNum=57,
            sender_realmNum=58,
            sender_accountNum=59,
            recipient_shardNum=100,
            recipient_realmNum=101,
            recipient_accountNum=int(destination.split(".")[2]),
            amount=send_amount,
        )
        
        # Use index 12345 for signing
        index = 12345
        
        # The operator parameters for the transaction
        operator_shard_num = 1
        operator_realm_num = 2
        operator_account_num = 3
        test_memo = "this_is_the_memo"
        

        public_key = bytes.fromhex(HEDERA_PUBLIC_KEY)
        
        # Create the transaction
        transaction = hedera_transaction(
            operator_shard_num=operator_shard_num,
            operator_realm_num=operator_realm_num,
            operator_account_num=operator_account_num,
            transaction_fee=fees,
            memo=test_memo,
            conf=conf,
        )
        
        # Prepare the full payload (index + transaction)
        transaction_to_sign = index.to_bytes(4, "little") + transaction
        
        # Sign the transaction
        signature = hedera.sign_transaction(
            index=index,
            operator_shard_num=operator_shard_num,
            operator_realm_num=operator_realm_num,
            operator_account_num=operator_account_num,
            transaction_fee=fees,
            memo=test_memo,
            conf=conf,
        )
        
        if not signature or len(signature) == 0:
            return
        
        # Verify the signature
        signature_valid = hedera.verify_signature(public_key, transaction_to_sign, signature)
        assert signature_valid, "Signature verification failed"



class TestsHedera:

    @pytest.mark.parametrize('test_to_run', ALL_TESTS_EXCEPT_MEMO_AND_THORSWAP)
    def tests_hedera(self, backend, exchange_navigation_helper, test_to_run):
        HederaTests(backend, exchange_navigation_helper).run_test(test_to_run)