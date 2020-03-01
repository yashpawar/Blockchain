from hashlib import sha256
import json
import time

from flask import Flask, request
import requests

# Block class
class Block:
    # constructor
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    # compute hashes
    def compute_hash(self):
        """
        A function that return the hash of the block contents.
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()
    @classmethod
    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        # check if hash of block is correct or not
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

class Blockchain:
    # difficulty of our PoW algorithm
    difficulty = 2

    def __init__(self):
        # transactions that will be added to the next block
        self.unconfirmed_transactions = []
        # blockchain
        self.chain = []

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        # no proof of work is done for creation of genesis block
        genesis_block = Block(0, [], 0, 0)
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    # get last block of blockchain
    @property
    def last_block(self):
        return self.chain[-1]

    # add new block
    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block
          in the chain match.
        """ 
        # get hash of last block
        previous_hash = self.last_block.hash

        # check if hash of previous block matches with previous_hash field entered in new block
        if (self.last_block.index + 1) != block.index:
            return False
        
        # check if hash of previous block matches with previous_hash field entered in new block
        if previous_hash != block.previous_hash:
            return False

        # check if calculated proof is valid or not
        if not Block.is_valid_proof(block, proof):
            return False

        # enter proof as hash of block
        block.hash = proof
        # append new block to the blockchain
        self.chain.append(block)
        return True
        


    

    # add new transaction to blockchain
    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)    
    
    # perform proof of work
    @staticmethod
    def proof_of_work(block):
        """
        Function that tries different values of nonce to get a hash
        that satisfies our difficulty criteria.
        """
        # initialize nonce to 0
        block.nonce = 0
        
        # compute hash of block
        computed_hash = block.compute_hash()
        # increment nonce until hash of block starts with 0...upto required difficulty
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        # return the hash with proper difficulty
        return computed_hash
        
    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        # enter data in block
        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        # computed hash is returned as proof
        proof = self.proof_of_work(new_block)
        # add this block tothe chain
        self.add_block(new_block, proof)
        # empty the list of unconfirmed transactions
        self.unconfirmed_transactions = []

        return True


app = Flask(__name__)

# the node's copy of blockchain
blockchain = Blockchain()

# genesis block of blockchain is created
blockchain.create_genesis_block()

# the address to other participating members of the network

peers = set()


# endpoint to return the node's copy of the chain.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data,
                       "peers": list(peers)})

# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["author", "content"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)
    for peer in peers:
        url = "{}pending_tx".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url,
                      data=json.dumps(tx_data, sort_keys=True),
                      headers=headers)
    

    return "Success", 201

# endpoint to query unconfirmed transactions
@app.route('/pending_tx',methods=['POST'])
def get_pending_tx():
    tx_data=request.get_json()
    blockchain.add_new_transaction(tx_data)
    return "Success",202

# endpoint to request the node to mine the unconfirmed
# transactions (if any). We'll be using it to initiate
# a command to mine from our application itself.
@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    if not blockchain.unconfirmed_transactions:
        return "No transactions to mine"
    else:
        # Making sure we have the longest chain before announcing to the network
        #chain_length = len(blockchain.chain)
        # perform consensus
        consensus()
        result = blockchain.mine()
        #if chain_length == len(blockchain.chain):
            # announce the recently mined block to the network
        announce_new_block(blockchain.last_block)
        return "Block #{} is mined.".format(blockchain.last_block.index)

def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    Other blocks can simply verify the proof of work and add it to their
    respective chains.
    """
    for peer in peers:
        url = "{}add_block".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url,data=json.dumps(block.__dict__, sort_keys=True),headers=headers)

# endpoint to add a block mined by someone else to
# the node's chain. The block is first verified by the node
# and then added to the chain.
@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


def consensus():
    """
    Our naive consnsus algorithm. If a longer valid chain is
    found, our chain is replaced with it.
    """    
    longest_chain = None
    current_len = len(blockchain.chain)
    global peers
    peer=set()
    for node in peers:
        response = requests.get('{}chain'.format(node))
        length = response.json()["length"]
        chain = response.json()["chain"]
        # implement consensus of peers
        peer.update(response.json()["peers"])
        peer.discard(request.host_url)
        
        if length > current_len:
            longest_chain=create_chain_from_dump(chain).chain
            current_len = length
            
    peers=peers.union(peer)
    
    if longest_chain is not None:
        blockchain.chain = longest_chain
        return True
    
    return False

def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue  # skip genesis block
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        proof = block_data['hash']
        added = generated_blockchain.add_block(block, proof)
        if not added:
            raise Exception("The chain dump is tampered!!")
    return generated_blockchain


# endpoint to add new peers to the network.
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    response = request.get_json()
    node_address=response["node_address"]
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    # update chain and the peers
        
    # peers.update(response["peers"])
    peers.update([node_address])
    # peers.discard(request.host_url)
    consensus()
    # Return the consensus blockchain to the newly registered node
    # so that he can sync
    # return json.dumps({"peers": list(peers)})
    return "Success", 200


@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    """
    Internally calls the `register_node` endpoint to
    register current node with the node specified in the
    request, and sync the blockchain as well as peer data.
    """
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400
    # request.host_url is sender's url
    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and obtain information
    response = requests.post(node_address + "/register_node",
                             data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        
        # update chain and the peers
        
        #peers.update(response.json()['peers'])
        peers.update([node_address+"/"])
        #peers.discard(request.host_url)
        consensus()
        
        return "{} connected to {}".format(request.host_url,node_address+"/"), 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code



# Uncomment this line if you want to specify the port number in the code
# take port as command line arguement
# to be edited later
import sys
app.run(port=sys.argv[1])
