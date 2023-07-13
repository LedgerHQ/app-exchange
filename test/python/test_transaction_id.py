from .apps.exchange import ExchangeClient, Rate, SubCommand

def test_transaction_id(backend):
    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SWAP)
    transaction_id = ex.init_transaction().data
    # Assert length
    assert len(transaction_id) == 10
    # Assert that we only received upper char ascii characters
    decoded = transaction_id.decode(errors='ignore')
    assert decoded.encode('ascii', errors='ignore') == transaction_id
    assert decoded.isalpha()
    assert decoded.isupper()

    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.SELL)
    transaction_id = ex.init_transaction().data
    # Assert length
    assert len(transaction_id) == 32

    ex = ExchangeClient(backend, Rate.FIXED, SubCommand.FUND)
    transaction_id = ex.init_transaction().data
    print(transaction_id)
    # Assert length
    assert len(transaction_id) == 32
