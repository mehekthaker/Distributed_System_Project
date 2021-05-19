"""
    Name: Mehek Piyush Thaker
    Student ID: 1001869277
"""
#---------------------------------------------------------------------------------------
"""
Importing socket module to establish the connection between client and server.
Importing os and threading modules to perform specific tasks
"""
import os
import socket
import threading
import select
import queue
import time 
from polling import TimeoutException, poll
import tkinter as tkinter
#----------------------------------------------------------------------------------------
# Initializing the Host and Port values
HOST = socket.gethostbyname(socket.gethostname())

# Port number to connect clients
PORT = 4456         

# To connect to backup server
BACKUPSERVER_PORT = 6692        

# Forming the ADDR tuple of HOST and PORT
ADDR = (HOST, PORT)
BACKUPSERVER_ADDR = (HOST, BACKUPSERVER_PORT)
SIZE = 4096
FORMAT = "utf-8"

# Creating a list to keep track of the connected users
users = []

# Creating a queue with no bounds
q = queue.Queue(maxsize=0)

# ----------------------------------------------------------------------------------------
# Retrieve the first word inserted inside the queue
def getNextWord(q):
    while not q.empty():
        next_word = q.get()
        q.task_done()
    return next_word  

"""
The function below handles the data sent and received to/from client by encoding and decoding the data respectively
using the UTF-8 format. This function sends and receives the data in the format CMD@MSG or CMD@FileName@Data where CMD specifies
the command on which there are conditions to perform specific tasks. For example, When the CMD value is UPLOAD then the file will be sent 
from client to server and the server will read the contents and compare the words in the file with the lexicon(list of misspelled words)
if the word in the file is in the list then it will surround that word inside square brackets and send that updated file back to client.
It also polls the client queue to retrieve a word from it if any and adds it to the lexicon such that there are no duplicate entries.
"""
def handle_client(conn, addr, backup_client):
    
    # Created a lexicon/dictionary(list) of commonly misspelled words(limited)
    initialLexicon = []
    lexicon = []
    
    window = tkinter.Tk()
    window.title("Server GUI")
    window.geometry("400x300")
    window.configure(bg="#cdc7be")
    
    # To kill the server        
    def exit():
        conn.close()
        os._exit(0)
        window.destroy()
    
    # To display the clients on server GUI    
    def printClients(userList):
        for index in range(len(userList)):
            listbox.insert(index, userList[index])

    def startServer():                
        while True:            
            try:    
                # Receiving data from client
                data = conn.recv(SIZE)
                
                # Splitting the incoming message
                data = data.decode(FORMAT)
                data = data.split("@")
                cmd = data[0]
                    
                if not data:
                    break        

                if cmd == "USER":
                    # CMD@MSG is the format followed so data[0] is the command, CMD and data[1] is the message. 
                    # In this case it is the username entered in the entry box.
                    # If the user is already in the users list then we need to notify the user to enter a different username and stop
                    # the flow of messages until a different username is used for connection. 
                    if data[1] in users:
                        conn.send(f"DUPLICATE@User {data[1]} already in use! Enter a different username".encode(FORMAT))
                        break

                    else:
                        # If the user is not in the list then we append it to the users list and send the username to server
                        users.append(data[1])
                        printClients(users)
                        send_data = f"USER@Client with username {data[1]} is connected!"
                        send_message = f"USER@{data[1]}"
                        conn.send(send_data.encode(FORMAT))
                        # backup_client.send(send_message.encode(FORMAT))
                        break

                # When CMD is UPLOAD the format in which the message is sent is CMD@FileName@Data. The incoming file is written at the server side
                # and then the temp file is opened and the file contents are read after which checking for its existence in the list named lexiconis done.
                # The word  which exists in the list is surrounded by the square brackets and written to new file. 
                # The previous temp file is deleted once the data is written to new file. After which this new file is sent to client.
                elif cmd == "STARTING":
                    send_message = f"START UPLOAD@Send the file"
                    conn.send(send_message.encode(FORMAT))
                    
                elif cmd == "UPLOAD":
                    name, text = data[1], data[2]
                    with open("tempfile.txt", "w+") as fileToWrite:
                        fileToWrite.write(text)
                    send_message = f"UPLOADED@Your file is successfully uploaded to Server!"
                    conn.send(send_message.encode(FORMAT))
                    
                    # Providing relative path of the file
                    newName = './server_socket/' + name
                    
                    # Writing the misspelled words surrounded with square brackets in new file by comparing it with lexicon files
                    with open("tempfile.txt") as fileToRead, open(newName, "w") as fileToUpdate, open("./server_socket/lexicon.txt", "r") as lexFile:
                        for line in lexFile.readlines():
                            line = line.split(',')
                            initialLexicon.append(line)
                        
                        for lexpos in initialLexicon:
                            lexicon.append(lexpos[0])
                            
                        for line in fileToRead:
                            flag = False
                            for word in line.split():
                                for lexword in lexicon:  
                                    if word == lexword: 
                                        flag = True
                                        fileToUpdate.write("[" + word + "] ")
                                if flag != True:
                                    fileToUpdate.write(word + " ")       
                                flag = False
                            fileToUpdate.write("\n")
            
                    # Removing the temp file 
                    os.remove("tempfile.txt") 
                        
                # Sending the contents of the updated file in the above mentioned message format
                elif cmd == "NOTIFIED":
                    with open(newName, "r") as f:
                        text = f.read()
                    send_data = f"RECEIVED@{name}@{text}"
                    conn.send(send_data.encode(FORMAT))
                    break
                
                # Indicates to start queue related operations    
                elif cmd == "QUEUE":
                    send_message = "START QUEUE@Start queue operations!"
                    conn.send(send_message.encode(FORMAT))
                
                # Used to upload the file whenever there is consequent file upload by a user  
                elif cmd == "UPLOAD AGAIN":
                    send_message = "START UPLOAD@Starting next upload!"
                    conn.send(send_message.encode(FORMAT))

                elif cmd == "LEXWORD":          
                    q.put(data[1])
                    
                    # Polling the client queue
                    next_word = poll(lambda: getNextWord(q), timeout=60, step=1)
                    
                    with open("./server_socket/lexicon.txt", "r") as fileRead:
                        for line in fileRead.readlines():
                            line = line.split(',')
                            initialLexicon.append(line)
                        
                        for lexpos in initialLexicon:
                            lexicon.append(lexpos[0])
                            
                    # Append the word entered by the user to the lexicon file
                    if next_word not in lexicon:
                        lexicon.append(next_word)
                        with open("./server_socket/lexicon.txt", "a+") as fileWrite:
                            fileWrite.write(next_word + ", \n")
                        
                        # Sends the updates to Backup Server        
                        send_update = f"UPDATEREPLICA@{next_word}"
                        print(send_update)
                        backup_client.send(send_update.encode(FORMAT))
                        break
                    
                elif cmd == "DISCONNECTED":
                    for user in users:
                        if user == data[1]:
                            users.remove(user)
                    listbox.delete('0', 'end')
                    printClients(users)
                    break
                
                # Closing the connection
                else:
                    print(f"[DISCONNECTED] {addr} disconnected")                    
                    conn.close()
                    os._exit(0)    

            except KeyboardInterrupt:
                print(f"[DISCONNECTED] {addr} disconnected")
                conn.close()
                
    def startServerThread():
        threadServer = threading.Thread(target=startServer)
        threadServer.start()
    
    frame1 = tkinter.Frame(master=window, width=100, height=100, bg="#cdc7be")
    fileBtn = tkinter.Button(window, text="Start processes", command=startServerThread, bg="#766161", fg="white")
    fileBtn.place(x=0,y=0)
    
    lexLabel = tkinter.Label(window, text = "Connected clients:", bg="#cdc7be")
    lexLabel.place(x=0, y=50)
    
    listbox = tkinter.Listbox(window)
    listbox.place(x=10, y=70)
    
    fileBtn = tkinter.Button(window, text="Quit", command = exit, bg="#766161", fg="white")
    fileBtn.place(x=100,y=0)
    frame1.pack()
            
    window.mainloop()
        
def main():

    print("[STARTING] Server is starting")
    
    # Create a TCP/IP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to port
    server.bind(ADDR)

    # Listen for incoming connections
    server.listen()
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}.")
    
    # Connecting to Backup Server
    backup_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    backup_client.connect(BACKUPSERVER_ADDR)
    print(f"Primary Server connected to Backup Server on {HOST}:{BACKUPSERVER_PORT}.")           
    
    while True:
        # Wait for a connection
        try:
            conn, addr = server.accept()
            
            #Creating thread for every new client connection in order to handle the client operations
            thread = threading.Thread(target=handle_client, args=(conn, addr, backup_client))
            thread.start()

            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
            
        except:
            server.shutdown(socket.SHUT_RDWR)
            conn.close()
            os._exit(0)
            
    else:
        conn.close() 
        os._exit(0)
    

if __name__ == "__main__":
    main()
    