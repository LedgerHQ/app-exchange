from typing import Dict
import sys
import pickle
from pathlib import Path

from google.protobuf import wrappers_pb2 as _wrappers_pb2
from hiero_sdk_python.hapi.services import basic_types_pb2, transaction_body_pb2, crypto_transfer_pb2, crypto_create_pb2

sys.path.append(f"{Path(__file__).parent.resolve()}/hedera_proto")
'''
Hedera Protobuf
'''

def hedera_transaction(
        operator_shard_num: int,
        operator_realm_num: int,
        operator_account_num: int,
        transaction_fee: int,
        memo: str,
        conf: Dict,
) -> bytes:
    operator = basic_types_pb2.AccountID(
        shardNum=operator_shard_num,
        realmNum=operator_realm_num,
        accountNum=operator_account_num,
    )

    hedera_transaction_id = basic_types_pb2.TransactionID(accountID=operator)

    transaction = transaction_body_pb2.TransactionBody(
        transactionID=hedera_transaction_id,
        transactionFee=transaction_fee,
        memo=memo,
        **conf
    )

    return transaction.SerializeToString()


def crypto_transfer_hbar_conf(
        sender_shardNum: int,
        sender_realmNum: int,
        sender_accountNum: int,
        recipient_shardNum: int,
        recipient_realmNum: int,
        recipient_accountNum: int,
        amount: int,
) -> Dict:

    hedera_account_id_sender = basic_types_pb2.AccountID(
        shardNum=sender_shardNum,
        realmNum=sender_realmNum,
        accountNum=sender_accountNum,
    )

    hedera_account_amount_sender = basic_types_pb2.AccountAmount(
        accountID=hedera_account_id_sender,
        amount=0,
    )

    hedera_account_id_recipient = basic_types_pb2.AccountID(
        shardNum=recipient_shardNum,
        realmNum=recipient_realmNum,
        accountNum=recipient_accountNum,
    )

    hedera_account_amount_recipient = basic_types_pb2.AccountAmount(
        accountID=hedera_account_id_recipient,
        amount=amount,
    )

    hedera_transfer_list = basic_types_pb2.TransferList(
        accountAmounts=[hedera_account_amount_recipient, hedera_account_amount_sender],
    )

    crypto_transfer = crypto_transfer_pb2.CryptoTransferTransactionBody(
        transfers=hedera_transfer_list,
        tokenTransfers=[],
    )

    return {"cryptoTransfer": crypto_transfer}

def crypto_create_account_conf(
        initialBalance: int,
        stakeTargetAccount: int = None,
        stakeTargetNode: int = None,
        declineRewards: bool = False,
) -> Dict:
    crypto_create_account = crypto_create_pb2.CryptoCreateTransactionBody(
        initialBalance=initialBalance
    )

    if stakeTargetAccount:
        account_id = basic_types_pb2.AccountID(
            shardNum=0, realmNum=0, accountNum=stakeTargetAccount
        )
        crypto_create_account = crypto_create_pb2.CryptoCreateTransactionBody(
            initialBalance=initialBalance,
            staked_account_id=account_id,
            decline_reward=declineRewards,
        )
    elif stakeTargetNode:
        crypto_create_account = crypto_create_pb2.CryptoCreateTransactionBody(
            initialBalance=initialBalance,
            staked_node_id=stakeTargetNode,
            decline_reward=declineRewards,
        )

    return {"cryptoCreateAccount": crypto_create_account}


def crypto_transfer_token_conf(
        token_shardNum: int,
        token_realmNum: int,
        token_tokenNum: int,
        sender_shardNum: int,
        sender_realmNum: int,
        sender_accountNum: int,
        recipient_shardNum: int,
        recipient_realmNum: int,
        recipient_accountNum: int,
        amount: int,
        decimals: int,
) -> Dict:
    hedera_token_id = basic_types_pb2.TokenID(
        shardNum=token_shardNum,
        realmNum=token_realmNum,
        tokenNum=token_tokenNum,
    )

    hedera_account_id_sender = basic_types_pb2.AccountID(
        shardNum=sender_shardNum,
        realmNum=sender_realmNum,
        accountNum=sender_accountNum,
    )

    hedera_account_amount_sender = basic_types_pb2.AccountAmount(
        accountID=hedera_account_id_sender,
        amount=0,
    )

    hedera_account_id_recipient = basic_types_pb2.AccountID(
        shardNum=recipient_shardNum,
        realmNum=recipient_realmNum,
        accountNum=recipient_accountNum,
    )

    hedera_account_amount_recipient = basic_types_pb2.AccountAmount(
        accountID=hedera_account_id_recipient,
        amount=amount,
    )

    hedera_transfer_list = basic_types_pb2.TransferList(
        accountAmounts=[],
    )

    decimalsUInt32 = _wrappers_pb2.UInt32Value(
        value=decimals,
    )

    hedera_token_transfer_list = basic_types_pb2.TokenTransferList(
        token=hedera_token_id,
        transfers=[hedera_account_amount_recipient, hedera_account_amount_sender],
        expected_decimals=decimalsUInt32,
    )

    crypto_transfer = crypto_transfer_pb2.CryptoTransferTransactionBody(
        transfers=hedera_transfer_list,
        tokenTransfers=[hedera_token_transfer_list],
    )

    return {"cryptoTransfer": crypto_transfer}


def crypto_transfer_hbar_conf(
        sender_shardNum: int,
        sender_realmNum: int,
        sender_accountNum: int,
        recipient_shardNum: int,
        recipient_realmNum: int,
        recipient_accountNum: int,
        amount: int,
) -> Dict:

    hedera_account_id_sender = basic_types_pb2.AccountID(
        shardNum=sender_shardNum,
        realmNum=sender_realmNum,
        accountNum=sender_accountNum,
    )

    hedera_account_amount_sender = basic_types_pb2.AccountAmount(
        accountID=hedera_account_id_sender,
        amount=0,
    )

    hedera_account_id_recipient = basic_types_pb2.AccountID(
        shardNum=recipient_shardNum,
        realmNum=recipient_realmNum,
        accountNum=recipient_accountNum,
    )

    hedera_account_amount_recipient = basic_types_pb2.AccountAmount(
        accountID=hedera_account_id_recipient,
        amount=amount,
    )

    hedera_transfer_list = basic_types_pb2.TransferList(
        accountAmounts=[hedera_account_amount_recipient, hedera_account_amount_sender],
    )

    crypto_transfer = crypto_transfer_pb2.CryptoTransferTransactionBody(
        transfers=hedera_transfer_list,
        tokenTransfers=[],
    )

    return {"cryptoTransfer": crypto_transfer}
