import hashlib
import json
from time import time
from flask import Flask, jsonify, request
from uuid import uuid4
from urllib.parse import urlparse
import requests

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.new_block(previous_hash='1', proof=100)
        self.nodes = set()

    def register_node(self, address):
        """
        Add new node to set of nodes
        :param address: <str> Address of node. (ex. 'http://192.24.3.4:5000')
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in Blockchain
        :param proof: <int> Output proof of Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        new_block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        self.current_transactions = []
        self.chain.append(new_block)
        return new_block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates new transaction for the next mined Block
        :param sender: <str> Address of the sender
        :param recipient: <str> Address of the recipient
        :param amount: <int> Amount in transaction
        :return: <int> The index of the Block that holds this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: <dict> Block being hashed
        :return: <str>
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        Proof of Work algorithm:
         - Find p' such that hash(pp') contains 1234 as leading digits, where p is
           the previous p'
         - p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Proof is valid if hash(last_proof, proof) contains 1234 as leading digits.
        :param last_proof: <int> previous proof
        :param proof: <int> current proof
        :return: True if correct, False if not
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "1234"

    def valid_chain(self, chain):
        """
        Determine if given blockchain is valid
        :param chain: <list> blockchain
        :return: <bool> True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            curr_block = chain[current_index]
            print(f'{last_block}')
            print(f'{curr_block}')
            print("\n-------------\n")
            # Check if hash of the block is correct
            if curr_block['previous_hash'] != self.hash(last_block):
                return False

            # Check if Proof of Work is correct
            if not self.valid_proof(last_block['proof'], curr_block['proof']):
                return False

            last_block = curr_block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """
        Consensus Algorithm that resolves conflicts by replacing chain with
        the longest one in the network.
        :return:  <bool> True if chain was replaced, False otherwise
        """

        neighbors = self.nodes
        new_chain = None
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbors:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True
        return False


# Instantiate Node
app = Flask(__name__)

# Globally unique address for node
node_id = str(uuid4()).replace('-', '')

blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Receive reward for finding the proof
    # Sender is "0" because this node has mined a new coin
    blockchain.new_transaction(
        sender="0",
        recipient=node_id,
        amount=1
    )

    # Forge the new Block and add to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block successfully Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values for transaction', 400

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

