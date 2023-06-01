import pytest

from .apps.exchange import ExchangeClient, Rate, SubCommand

def test_transaction_id(backend, firmware):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    ex.init_transaction()
    # Assert length
    assert len(ex._transaction_id) == 10
    # Assert that we only received upper char ascii characters
    decoded = ex._transaction_id.decode(errors='ignore')
    assert decoded.encode('ascii', errors='ignore') == ex._transaction_id
    assert decoded.isalpha()
    assert decoded.isupper()

    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SELL)
    ex.init_transaction()
    # Assert length
    assert len(ex._transaction_id) == 32

    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.FUND)
    ex.init_transaction()
    print(ex._transaction_id)
    # Assert length
    assert len(ex._transaction_id) == 32
