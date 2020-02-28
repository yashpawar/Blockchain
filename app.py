import json
import requests
from flask import Flask,request


def fetch(CONNECTED_NODE_ADDRESS):
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)
        #posts = sorted(content, key=lambda k: k['timestamp'],reverse=True)
        return content

def submit(CONNECTED_NODE_ADDRESS,post_content,author):
    """
    function create a new transaction via our application.
    """

    post_object = {'author': author,'content': post_content}

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return True

def mine(CONNECTED_NODE_ADDRESS):
    get_chain_address = "{}/mine".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        print(response.content)

def register(CONNECTED_NODE_ADDRESS,Remote_node):


    post_object = {"node_address": Remote_node}

    # Submit a transaction
    new_tx_address = "{}/register_with".format(CONNECTED_NODE_ADDRESS)

    response=requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})

    return response.content

while 1:
    print ("Enter your command")
    print ("1:Register")
    print ("2:fetch")
    print ("3:submit")
    print ("4:mine")
    print ("5:exit")
    res=input()
    if res=='5':
        break
    # CONNECTED_NODE_ADDRESS: The node with which our application interacts, there can be multiple such nodes as well.
    CONNECTED_NODE_ADDRESS=input("Enter node to connect to: ")
    if res=='1':
        Remote_node=input("Enter node to register connected node with: ")
        print(register(CONNECTED_NODE_ADDRESS,Remote_node))
    if res=='2':
        print(fetch(CONNECTED_NODE_ADDRESS))
    if res=='3':
        post_content=input("Enter data: ")
        author=CONNECTED_NODE_ADDRESS
        if submit(CONNECTED_NODE_ADDRESS,post_content,author):
            print("submission successful")
    if res=='4':
        mine(CONNECTED_NODE_ADDRESS)
