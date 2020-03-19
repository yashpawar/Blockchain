#####################chat mode#########################
from threading import Thread
from tkinter import *
def get_chat():
    while 1:
        text=""
        ch=get_chain().get('chain')
        #ch=blockchain.chain.copy()
        for bl in ch:
            txs=bl.get(transactions)
            for tx in txs:
                text+=str(str(tx.get('peer'))+" : "+str(tx.get('data'))+"\n")
        T.config(state='normal')
        T.delete(1.0, END)
        T.insert(END,text)
        T.config(state='disabled')        
        time.sleep(0.25)
 
master =Tk()
master.title('Chat') 

S = Scrollbar(master)
S.pack(side=RIGHT,fill=Y)

T=Text(master, height=10, width=50)
T.pack()
S.config(command=T.yview)
T.config(yscrollcommand=S.set)

tc=Thread(target = get_chat)
tc.daemon=True
tc.start()
T2=Text(master, height=2, width=50)
T2.pack()
def send():
    new_transaction({'peer':CONNECTED_NODE_ADDRESS,'data':T2.get("1.0",'end-1c')})
    T2.delete(1.0,END)
send = Button(master, text='Send', width=25, command=send) 
send.pack()
Tr=Text(master, height=1, width=50)
Tr.pack()
def reg():
    register_with_existing_node("http://"+Tr.get("1.0",'end-1c')+":"+port+"/")
reg = Button(master, text='Register', width=25, command=reg)

reg.pack()
def stop():
    master.destroy
    sys.exit()
stop = Button(master, text='Stop', width=25, command=stop) 
stop.pack()
master.mainloop() 
#############################################################
