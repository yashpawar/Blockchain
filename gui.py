import cv2
from tkinter import *
from PIL import Image, ImageTk
from datetime import datetime
from threading import Thread
import time
from qd_new import *
from node import *

def add_label():
    global save
    lbl=Tr.get("1.0",'end-1c')
    if lbl != '':
        filename=str(lbl)+datetime.now().strftime("_%m_%d_%Y_%H_%M_%S")+'_'+str(my_id)+'.jpg'
        cv2.imwrite(filename,save)
        new_transaction({'peer':CONNECTED_NODE_ADDRESS,'name':filename,'img':get_image(filename)})
             
capt=1        
#Set up GUI
window = Tk()  #Makes main window
window.title('GUI')
#Graphics window
imageFrame = Frame(window, width=600, height=500)
imageFrame.grid(row=0, column=0, padx=10, pady=2)

#Capture video frames
lmain = Label(imageFrame)
lmain.grid(row=0, column=0)


cap = cv2.VideoCapture(0)


def main():      
    global capt
    _, img = cap.read()
    img = cv2.flip(img, 1)
    if capt==0:
        cv2.putText(img, str(pred_class), (100,50) , cv2.FONT_HERSHEY_SIMPLEX ,2, (0,255,0), 2)
        img=drawpts(img)
    else:
        img=ip(img)
    cv2image = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    imgarr = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=imgarr)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)
    lmain.after(10,main)
 

def setcapt():
    global capt
    global pred_class
    global save
    save,pred_class=cv()
    capt=0
    if pred_class==-1:
        clearall()

def clearall():
    clear()
    global capt
    capt=1

w = Label(window, text='Label') 
w.grid(row=0, column=1, padx=10, pady=2)
Tr=Text(window, height=1, width=5)
Tr.grid(row=0, column=2, padx=10, pady=2)
btnl = Button(window, text="Identify", command=add_label)
btnl.grid(row=0, column=3, padx=10, pady=2)

btn2 = Button(window, text="Done", command=setcapt)
btn2.grid(row=1, column=1, padx=10, pady=2)
btn3 = Button(window, text="Clear", command=clearall)
btn3.grid(row=1, column=2, padx=10, pady=2)

####################
def reg():
    register_with_existing_node("http://"+Tr.get("1.0",'end-1c')+":"+port+"/")
reglbl = Label(window, text='Peer') 
reglbl.grid(row=2, column=1, padx=10, pady=2)
Addr=Text(window, height=1, width=5)
Addr.grid(row=2, column=2, padx=10, pady=2)
reg = Button(window, text="Register", command=reg)
reg.grid(row=2, column=3, padx=10, pady=2)
####################

def stop():
    window.destroy
    sys.exit()
stop = Button(window, text="Exit", command=stop) 
stop.grid(row=1, column=3, padx=10, pady=2)

main()

window.mainloop()  #Starts GUI
