"""
    Name: Mehek Piyush Thaker
    Student ID: 1001869277
"""
#---------------------------------------------------------------------------------------
"""
Importing socket module to establish the connection between client and server.
Importing os and threading modules to perform specific tasks
"""
import socket
import threading
import os
import queue
import time 
from polling import TimeoutException, poll

BACKUP_HOST = socket.gethostbyname(socket.gethostname())
# Port to connect with the primary server
BACKUP_PORT = 6692

# Port to connect the clients
CLIENT_PORT = 8857     

# Address tuple of host and port for both the connections
CLIENT_ADDR = (BACKUP_HOST, CLIENT_PORT)
BACKUPSERVER_ADDR = (BACKUP_HOST, BACKUP_PORT)
SIZE = 4096
FORMAT = "utf-8"

# Creating a list to keep track of the connected users
users = []

# Creating a queue with no bounds
q = queue.Queue(maxsize=0)

# Gets the next word from the queue
def getNextWord(q):
    while not q.empty():
        next_word = q.get()
        q.task_done()
    return next_word

def handle_client(conn, client_addr):
    initialLexicon = []
    lexicon = []
    
    while True:
        try:
            data = conn.recv(SIZE)
            
            if not data:
                break
            
            data = data.decode(FORMAT)
            data = data.split("@")
            cmd = data[0]
            
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
                    send_data = f"USER@Client with username {data[1]} is connected!"
                    conn.send(send_data.encode(FORMAT))

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
                newName = './backupServer_socket/' + name
                    
                # Writing the misspelled words surrounded with square brackets in new file by comparing it with lexicon files
                with open("tempfile.txt") as fileToRead, open(newName, "w") as fileToUpdate, open("./backupServer_socket/lexicon.txt", "r") as lexFile:
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
                                    print("Inside if")
                                    flag = True
                                    fileToUpdate.write("[" + word + "] ")
                                    print("Square brackets done")
                            if flag != True:
                                fileToUpdate.write(word + " ")
                                print("When no match in lexicon")        
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
                
                with open("./backupServer_socket/lexicon.txt", "r") as fileRead:
                    for line in fileRead.readlines():
                        line = line.split(',')
                        initialLexicon.append(line)
                        
                    for lexpos in initialLexicon:
                        lexicon.append(lexpos[0])
                            
                    # Append the word entered by the user to the lexicon file
                    if next_word not in lexicon:
                        lexicon.append(next_word)
                        with open("./backupServer_socket/lexicon.txt", "a+") as fileWrite:
                            fileWrite.write(next_word + ", \n")
                    
            else:
                print(f"[DISCONNECTED] {client_addr} disconnected now!")
                conn.close()
                os._exit(0)
                
        except:
                print(f"[DISCONNECTED] {client_addr} disconnected")
                conn.close() 
                break
                
# Gets the updates from the primary server
def handle_primary_server(backup_conn, backup_addr, client_conn):
    
    while True:
        try:
            updates = backup_conn.recv(SIZE)
            if not updates:
                break
               
            # Splitting the incoming message
            updates = updates.decode(FORMAT)
            updates = updates.split("@")
            cmd = updates[0] 
                    
            if cmd == "UPDATEREPLICA":
                with open("./backupServer_socket/lexicon.txt", "a+") as fileWrite:
                    fileWrite.write(updates[1] + ", \n")
                            
            if cmd == "USER":
                users.append(updates[1])
                print(users)
        
        except:
            send_message = "Primary Server Crashed!"
            print(send_message)
            backup_conn.close()
            break
    
    # Connects the clients to backup server after primary server crashes
    acceptingConnectionFromClients(client_conn)            
    
# Handles connection with the primary server        
def acceptingConnectionFromPrimaryServer(backup_server, client_conn):   
    while True:       
        backup_conn, backup_addr = backup_server.accept()
        handle_primary_server(backup_conn, backup_addr, client_conn)

# Handles connection with all the clients        
def acceptingConnectionFromClients(client_conn):
    while True:
        conn, client_addr = client_conn.accept() 
        thread = threading.Thread(target=handle_client, args=(conn, client_addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")    

        
def main():
    
    print("[STARTING] Backup Server is starting")
    
    # Create a TCP/IP socket
    backup_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the socket to port
    backup_server.bind(BACKUPSERVER_ADDR)
    client_conn.bind(CLIENT_ADDR)

    # Listen for incoming connections
    backup_server.listen()
    print(f"[LISTENING] Server is listening on {BACKUP_HOST}:{BACKUP_PORT}.")
    
    client_conn.listen()
    print(f"[LISTENING] Server is listening on {BACKUP_HOST}:{CLIENT_PORT}.")
    
    acceptingConnectionFromPrimaryServer(backup_server, client_conn)


if __name__ == "__main__":
    main()