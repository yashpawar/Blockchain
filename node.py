from hashlib import sha256
import json
import time
import sys,os
#from threading import Thread
#import uuid
#print(hex(uuid.getnode()))

from flask import Flask, request
import requests
import socket
from threading import Thread

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
        
        # Now that we have accepted the block, we will remove the transactions
        # confirmed from list of unconfirmed transactions
        y=[x for x in self.unconfirmed_transactions if x not in block.transactions]
        self.unconfirmed_transactions=y
        
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
        # self.unconfirmed_transactions = []
        
        """
        
        chain_data = []
        for block in self.chain:
            chain_data.append(block.__dict__)
        # save the blockchain in ./mined [Make sure to create this directory]
        with open("./mined/baron_blockchain", "w") as file_:
            print("New Block mined and wrote sucessfully")
            file_.write(str(base64.b64encode(b''+str.encode(str(chain_data))) ))
        """

        return True

##########################################################################################################
host='0.0.0.0'
port='8000'
node_type=int(sys.argv[1])
Block_size=1

# the node's copy of blockchain
blockchain = Blockchain()

# genesis block of blockchain is created
blockchain.create_genesis_block()

# address of this node
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('192.168.43.100', 80))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
CONNECTED_NODE_ADDRESS="http://"+get_ip()+":"+port+"/"
# the address to other participating members of the network
#peers = set()
peers={CONNECTED_NODE_ADDRESS:node_type}
miners={}
if node_type==1:
    miners={CONNECTED_NODE_ADDRESS:1}

   


app = Flask(__name__)

###suppress output
import os
import logging

logging.getLogger('werkzeug').disabled = True
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

###############################################################################


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
                       #"peers": list(peers)})
                       "peers":peers,
                       "miners":miners})

# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain
#@app.route('/new_transaction', methods=['POST'])
def new_transaction(tx_data):
#    tx_data = request.get_json()
#    required_fields = ["author", "content"]

#    for field in required_fields:
#        if not tx_data.get(field):
#            return "Invalid transaction data", 404

    tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)
    announce_new_transaction(tx_data)
    return "submission successful"

def announce_new_transaction(tx_data):
    """
    A function to announce to the network new transaction.
    """
    for peer in miners:
        if peer == CONNECTED_NODE_ADDRESS:
            continue
        url = "{}pending_tx".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url,data=json.dumps(tx_data, sort_keys=True),headers=headers)

# endpoint to accept unconfirmed transactions from other nodes
@app.route('/pending_tx',methods=['POST'])
def get_pending_tx():
    sender="http://"+request.remote_addr+":"+port+"/"
    # added new functionality to check wether incoming transaction is from valid peer
    if not sender in peers:
        return "Rejected",400
    tx_data=request.get_json()
    blockchain.add_new_transaction(tx_data)
    return "Success",202

# endpoint to request the node to mine the unconfirmed
# transactions (if any). We'll be using it to initiate
# a command to mine from our application itself.
#@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    if node_type==0:
        return "I cannot mine"
    
    while list(miners.keys())[int(blockchain.last_block.hash,16) % (len(miners))] != CONNECTED_NODE_ADDRESS:
        #return "Not Me",400
        pass
    while len(blockchain.unconfirmed_transactions)<Block_size:
        pass
    
    # Making sure we have the longest chain before announcing to the network
    #chain_length = len(blockchain.chain)
    # perform consensus
    consensus()
    #Thread(target = mine).start()
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
        if peer == CONNECTED_NODE_ADDRESS:
            continue
        url = "{}add_block".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url,data=json.dumps(block.__dict__, sort_keys=True),headers=headers)

# endpoint to add a block mined by someone else to
# the node's chain. The block is first verified by the node
# and then added to the chain.
@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    sender="http://"+request.remote_addr+":"+port+"/"
    # added new functionality to check wether incoming block is from valid miner
    if not sender in miners:
        return "Rejected",400

    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"])

    proof = block_data['hash']
    blockchain.add_block(block, proof)

    return "Block added to the chain", 201


def consensus():
    """
    Our naive consnsus algorithm. If a longer valid chain is
    found, our chain is replaced with it.
    """    
    longest_chain = None
    current_len = len(blockchain.chain)
    #peer=set()
    for node in peers:
        response = requests.get('{}chain'.format(node))
        length = response.json()["length"]
        chain = response.json()["chain"]
        # implement consensus of peers
        # peer.update(response.json()["peers"])
        # peer.discard(request.host_url)
        #peers.update(response.json()["peers"])
        
        
        if length > current_len:
            longest_chain=create_chain_from_dump(chain).chain
            current_len = length
            
    #peers=peers.union(peer)
    
    if longest_chain is not None:
        blockchain.chain = longest_chain
        return True
    
    return False

def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue  # skip genesis block as no proof of work was done for it
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
    #remote_node_address=response["node_address"]
    #remote_node_type=response["node_type"]
    #if not node_address:
    #    return "Invalid data", 400

    # Add the node to the peer list
    # update chain and the peers
        
    # peers.update(response["peers"])
    #peers.update([remote_node_address])
    #peers.update({CONNECTED_NODE_ADDRESS:node_type})
    #if node_type==1:
    #    miners.update({CONNECTED_NODE_ADDRESS:node_type})
    announce_new_peer(response)
    peers.update(response)
    if list(response.values())[0]==1:
        miners.update(response)

    
    # peers.discard(request.host_url)
    consensus()
    # Return the consensus blockchain to the newly registered node
    # so that he can sync
    # return json.dumps({"peers": list(peers)})
    # return "Success", 200
    return get_chain()


#@app.route('/register_with', methods=['POST'])
def register_with_existing_node(node_address):
    """
    Internally calls the `register_node` endpoint to
    register current node with the node specified in the
    request, and sync the blockchain as well as peer data.
    """
    #response= request.get_json()
    #node_address= response["node_address"]
    #node_type=response["node_type"]
    #if not node_address:
    #    return "Invalid data", 400
    #if node_address+"/"==request.host_url:
    #    return "Invalid data", 400
    # request.host_url is sender's url
    #data = {"node_address": request.host_url,"node_type":node_type}
    data={CONNECTED_NODE_ADDRESS:node_type}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and obtain information
    response = requests.post(node_address + "register_node",
                             data=json.dumps(data), headers=headers)
    

    if response.status_code == 200:
        
        # update chain and the peers
        
        #peers.update(response.json()['peers'])
        #peers.update([node_address+"/"])
        # peers[node_address+"/"]=
        #peers.discard(request.host_url)
        #consensus()
        global peers
        global miners
        blockchain.chain=create_chain_from_dump(response.json()["chain"]).chain
        peers=response.json()["peers"].copy()
        miners=response.json()["miners"].copy()
        return "connected"
    else:
        # if something goes wrong, pass it on to the API response
        return "failed"

def announce_new_peer(new_peer):
    """
    A function to announce to the network new transaction.
    """
    for peer in peers:
        if (peer == CONNECTED_NODE_ADDRESS) or (peer == new_peer.keys()):
            continue
        url = "{}add_peer".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url,data=json.dumps(new_peer, sort_keys=True),headers=headers)

# endpoint to accept unconfirmed transactions from other nodes
@app.route('/add_peer',methods=['POST'])
def add_peer():
    sender="http://"+request.remote_addr+":"+port+"/"
    # added new functionality to check wether incoming peer data block is from valid miner
    if not sender in miners:
        return "Rejected",400
    response=request.get_json()
    if list(response.values())[0]==1:
        miners.update(response)
    peers.update(response)
    return "Success",202

# Uncomment this line if you want to specify the port number in the code
# take port as command line arguement
# to be edited later


def run_app():
    app.run(host=host,port=port,threaded=True)
    
t1=Thread(target = run_app)
t1.daemon=True
t1.start()

 
time.sleep(1)
# miner guy running in parallel for a miner node
def mining():
    while 1:
        mine_unconfirmed_transactions()
if node_type:
    t2=Thread(target = mining)
    t2.daemon=True
    t2.start()
    

def option_menu():
    while 1:
        print("___________________________________________________________________________________")
        print ("1:Register")
        print ("2:fetch")
        print ("3:submit")
        print ("4:exit")
        res=input()
        if res=='1':
            Remote_node="http://"+input("Enter node to register connected node with: ")+":"+port+"/"
            print(register_with_existing_node(Remote_node))
        if res=='2':
            print(get_chain())
        if res=='3':
            print(new_transaction({CONNECTED_NODE_ADDRESS:input("Enter data: ")}))
        if res=='4':
            sys.exit()
        print("___________________________________________________________________________________")
        
option_menu()


