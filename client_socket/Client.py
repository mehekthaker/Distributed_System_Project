"""
    Name: Mehek Piyush Thaker
    Student ID: 1001869277
"""
#---------------------------------------------------------------------------------------
"""
Importing socket module to establish the connection between client and server.
Importing tkinter modules like filedialog, in order to do file operations and messagebox module to
display or notify the user with prompts. Importing queue and threading module.
"""
import socket
import tkinter as tkinter
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import queue
import os
import threading
from queue import Empty
#----------------------------------------------------------------------------------------

# Initializing the Host and Port values
HOST = socket.gethostbyname(socket.gethostname())
# Port to connect primary server
PORT = 4456 
# Port to connect backup server    
BACKUP_PORT = 8857      

#Initializing queue with no bounds
q = queue.Queue(maxsize=0)

# Forming the ADDRESS tuple of HOST and PORT for both the connections
ADDR = (HOST, PORT)
BACKUP_ADDR = (HOST, BACKUP_PORT)
FORMAT = "utf-8"
SIZE = 4096   

#Initializing command list
cmdList = []

def main():

    # Creating a TCP/IP socket for connecting client with primary server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    
    # Creating a TCP/IP socket for connecting client with backup server
    backup_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    backup_server.connect(BACKUP_ADDR)

    # Creating a GUI window and specifying the dimensions of the window
    window = tkinter.Tk()
    window.title("Client GUI")
    window.geometry("400x300")
    window.configure(bg="#cdc7be")
    
    
    # When username is entered into the input text box of tkinter (which is using entry)
    def enterUser(arg = None):
        username = userEntry.get()
        if username:
            try:
                client.send(f"USER@{username}".encode(FORMAT))
                # Calling the function to register the username with primary server
                sendOverConn(q, False) 
                
            except:
                backup_server.send(f"USER@{username}".encode(FORMAT))
                # Calling the function to register the username with backup server
                backupConnection(q, False)       

    # Using frames to align the text and buttons
    frame1 = tkinter.Frame(master=window, width=100, height=100, bg="#cdc7be")

    # Just a plain text on GUI telling what to do next
    userLabel = tkinter.Label(window, text = "Enter a Username:", bg="#cdc7be")
    userLabel.place(x=0, y=0, width=100)

    # Entry is used to take the user input. Here, username is taken as the input
    userEntry = tkinter.Entry(window, bd=5)
    userEntry.place(x=100, y=0, width=200)

    frame1.pack()


    frame2 = tkinter.Frame(master=window, width=100, height=50, bg="#cdc7be")

    # Sends the username to server once this button is clicked
    btn = tkinter.Button(window, text="Connect!", command=enterUser, bg="#766161", fg="white")
    btn.place(height=30, width=100, x=0, y=30)

    frame2.pack()

    
    def fileDialog():
        # To open only text files and get their file path
        path = filedialog.askopenfilename(initialdir="/", filetype=[("Text files", "*.txt")])
        
        # Displays the file path on GUI
        pathlabel.config(text=path, bg="#cdc7be")
        pathlabel.place(x=100, y=150)
        
        send_message = f"STARTING@Uploading is started!"
        
        try:
            client.send(send_message.encode(FORMAT))
            #Calling the function to upload the file to server
            sendOverConn(q, path)
        except:
            backup_server.send(send_message.encode(FORMAT))
            #Calling the function of backup server to upload the file to backup server
            backupConnection(q, path)   
               
    """
    This function below sends and receives the data in the format CMD@MSG or CMD@FileName@Data by encoding
    and decoding the data sent or received respectively using the UTF-8 format. Depending on the CMD (CMD = command) specific operations are
    performed. For example, if the CMD value is RECEIVED then we will write the contents of the file sent by the server
    to client. There are appropriate messagebox used which will notify or prompt the user when needed. It also performs queue related operations.
    """
    def sendOverConn(q, path):
        while True:

            try:
                # Receiving the data sent from server
                data = client.recv(SIZE)
                    
                if not data:
                    print("No data found")
                    break               

                # Splitting to get the cmd and msg values to perform further operations
                data = data.decode(FORMAT)
                datalist = data.split("@")
                cmd, msg = datalist[0], datalist[1]
                    
                # Inserting the commands to the list
                cmdList.append(cmd)
                    
                # This means that when a user is connected then only it will be able to send the file
                if cmd == "USER":
                    messagebox.showinfo("Message", msg)
                    break
                    
                elif "USER" in cmdList and cmd == "START QUEUE":
                            
                    if not q.empty():
                        next_word = q.get()
                        q.task_done()
                        send_word = f"LEXWORD@{next_word}"
                        client.send(send_word.encode(FORMAT))
                        msg = f"Word retrieved by the Server: {next_word}"
                        messagebox.showinfo("Poll Received!", msg)
                        break
                        
                elif "USER" in cmdList and cmd == "START UPLOAD":    
                                                    
                    if path:
                        # Reading the file which is on the above mentioned file path
                        with open(path, "r") as fileToRead:
                            data = fileToRead.read()

                        #Taking only the name of the file
                        filename = path.split("/")[-1]

                        # Encoding and sending the data in the format CMD@FileName@Data
                        send_data = f"UPLOAD@{filename}@{data}"
                        client.send(send_data.encode(FORMAT))
                    
                # Notifying the user of successful file upload to server
                elif cmd == "UPLOADED":
                    messagebox.showinfo("Message", msg)
                    send_message = f"NOTIFIED@Notified about uploading done!"
                    client.send(send_message.encode(FORMAT))
                                    
                # If CMD is RECEIVED then transfer the file with spell check sequence to client from server and notify the same to user
                elif cmd == "RECEIVED":
                    name, text = datalist[1], datalist[2]
                    with open(name, "w+") as f:
                        f.write(text)
                    messagebox.showinfo("Message", "Spell Check Sequence Completed!") 
                    break

                # This is when the client with same username is trying to connect to server and terminates the connection      
                elif cmd == "DUPLICATE":
                    messagebox.showinfo("Message", msg)
                    break 
                
            except: 
                for i in range(3):
                    messagebox.showinfo("Message", "Primary Server is not responding!") 
                client.close()
                break
            
        else:      
            client.close()
            os._exit(0)           

            
    def backupConnection(q, path):
        while True:
            try:
                # Receiving the data sent from backup server
                backup_data = backup_server.recv(SIZE)
                
                if not backup_data: 
                    break
                
                # Splitting to get the cmd and msg values to perform further operations
                backup_data = backup_data.decode(FORMAT)
                backup_data_list = backup_data.split("@")
                cmd, msg = backup_data_list[0], backup_data_list[1]
                    
                # Inserting the commands to the list
                cmdList.append(cmd)
                
                # This means that when a user is connected then only it will be able to send the file
                if cmd == "USER":
                    messagebox.showinfo("Message", msg)
                    break
                    
                elif "USER" in cmdList and cmd == "START QUEUE":
                            
                    if not q.empty():
                        next_word = q.get()
                        q.task_done()
                        send_word = f"LEXWORD@{next_word}"
                        backup_server.send(send_word.encode(FORMAT))
                        msg = f"Word retrieved by the Server: {next_word}"
                        messagebox.showinfo("Poll Received!", msg)
                        break
                        
                elif "USER" in cmdList and cmd == "START UPLOAD":    
                                                    
                    if path:
                        # Reading the file which is on the above mentioned file path
                        print("Path is present in the sendOverConn function")
                        with open(path, "r") as fileToRead:
                            data = fileToRead.read()

                        #Taking only the name of the file
                        filename = path.split("/")[-1]

                        # Encoding and sending the data in the format CMD@FileName@Data
                        send_data = f"UPLOAD@{filename}@{data}"
                        backup_server.send(send_data.encode(FORMAT))
                    
                # Notifying the user of successful file upload to server
                elif cmd == "UPLOADED":
                    messagebox.showinfo("Message", msg)
                    send_message = f"NOTIFIED@Notified about uploading done!"
                    backup_server.send(send_message.encode(FORMAT))
                                    
                # If CMD is RECEIVED then transfer the file with spell check sequence to client from server and notify the same to user
                elif cmd == "RECEIVED":
                    name, text = backup_data_list[1], backup_data_list[2]
                    with open(name, "w+") as f:
                        f.write(text)
                    messagebox.showinfo("Message", "Spell Check Sequence Completed!") 
                    break

                # This is when the client with same username is trying to connect to server and terminates the connection      
                elif cmd == "DUPLICATE":
                    messagebox.showinfo("Message", msg)
                    break
                           
            except:
                backup_server.close()
                os._exit(0)
                                        
    # To disconnect the client
    def exit():
        username = userEntry.get()
        send_message = f"DISCONNECTED@{username}"
        print(send_message)
        try:
            client.send(send_message.encode(FORMAT))
            client.close()
        except:
            backup_server.close()
        os._exit(0)
        window.destroy()
    
    frame3 = tkinter.Frame(master=window, width=100, height=25, bg="#cdc7be")
    fileLabel = tkinter.Label(window, text = "Choose a file from your location:", bg="#cdc7be")
    fileLabel.place(x=0,y=100)

    # To choose the files that need to be sent from the computer location
    fileBtn = tkinter.Button(window, text="Browse", command = fileDialog, bg="#766161", fg="white")
    fileBtn.place(x=200,y=100)

    # For user to explicitly logout or terminate the connection
    fileBtn = tkinter.Button(window, text="Quit", command = exit, bg="#766161", fg="white")
    fileBtn.place(x=300,y=100)
    frame3.pack()

    pathlabel = tkinter.Label(window)
    pathlabel.pack() 

    frame4 = tkinter.Frame(master=window, width=100, height=25, bg="#cdc7be")
    
    lexLabel = tkinter.Label(window, text = "Enter additions to lexicon:", bg="#cdc7be")
    lexLabel.place(x=0, y=200)
    
    lexEntry = tkinter.Entry(window, bd=5)
    lexEntry.place(x=150, y=200, width=200)
    
    #Insert the words entered by user inside the queue
    def enterWord(word):
        if word:
            q.put(word)
            
    def createThreadsForLex():
        word = lexEntry.get() 
        
        # Creating threads to avoid tkinter from entering the infinite loop 
        t = threading.Thread(target=enterWord, args=(word,))
        t.start()
        t.join()
        
        # Deletes the word once entered and button click event performed by the user
        lexEntry.delete('0', 'end')
        
        send_message = "QUEUE@Performing queue operations!"
        try:
            client.send(send_message.encode(FORMAT))
            # Calling the function to retrieve the words in the queue
            sendOverConn(q, False)
        except:
            backup_server.send(send_message.encode(FORMAT))
            # Calling the function of backup server to retrieve the words in the queue
            backupConnection(q, False)
        
    # To choose the files that need to be sent from the computer location
    lexBtn = tkinter.Button(window, text="Add", command = createThreadsForLex, bg="#766161", fg="white")
    lexBtn.place(x=0, y=225)
    
    frame4.pack()  
    
    # Must be used for the window to appear
    window.mainloop()
      
if __name__ == "__main__":
    main()

