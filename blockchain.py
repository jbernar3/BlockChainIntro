class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

    # Create new Block and adds to the chain
    def new_block(self):
        pass

    # Adds new transaction to list of transactions
    def new_transaction(self):
        pass

    # Hash a block
    @staticmethod
    def hash(block):
        pass

    # Returns the last Block in the chain
    @property
    def last_block(self):
        pass