# Distributed System Project
## Table of Contents
1. [Client Functions](#client-functions)
2. [Primary Server Functions](#primary-server-functions)
3. [Backup Server Functions](#backup-server-functions)

## Client Functions
**Startup**
1. Prompt the user to input a username.
2. Connect to the server over a socket and register the username
    a. When the client is connected, the user should be notified of the active connection.
    b. If the provided username is already in use, the client should disconnect and prompt the user to input a
       different username.
3. Simultaneously handle ‘File Upload’ and ‘Lexicon Additions’ until manually killed by the user.

**File Upload**
1. Upload the user-supplied text file to the server and notify the user of upload completion.
2. Wait until the server has completed checking the file for spelling errors.
3. Receive the updated text file from the server and notify the user that the spell check sequence has completed.
4. Return to Step 1 of ‘File Upload’ until manually terminated by the user.

**Lexicon Additions**
1. Present the user with the ability to enter additions to the lexicon via the GUI.
2. Place the entered text into a queue. There should not be an upper bound on the size of the queue.
3. When polled by the server, the client should indicate that a poll was received and print the contents of the
queue retrieved by the server (if any).
4. After polling, the client should clear the contents of the queue (if any).
5. Return to Step 1 of ‘Lexicon Additions’ until manually terminated by the user.

**On Primary Server Failure**
1. Clients should recognize that the primary server is not responding and print a notification to their GUIs.
2. Connect to the backup server and notify the user of the switch to a backup.
3. Resume 'File Upload' and 'Lexicon Additions' until manually terminated by the user.

## Primary Server Functions
The server should support three concurrently connected clients. The server should indicate which of those clients are
presently connected on its GUI. The server will execute the following sequence of steps:

**Startup**
1. Startup and listen for incoming connections.
2. Print that a client has connected, and:
  a. If the client’s username is available (e.g., not currently being used by another client), fork a thread to
     handle that client; or,
  b. If the username is in use, reject the connection from that client.
3. Simultaneously handle ‘Spell Check’ and ‘Polling’ until manually killed by the user.

**Spell Check**
1. Receive a user-supplied text file from the client.
2. Check all words in the user-supplied text file against the lexicon and identify matches.
3. Return the updated file to the client.
4. Return to Step 1 of ‘Spell Check’ until manually killed by the user.

**Polling**
1. Every 60 seconds, poll clients for the status of their queues.
2. Retrieve contents from queue, if any.
3. Compare retrieved contents against present contents of lexicon and remove duplicates, if any.
4. Apply retrieved contents to lexicon.
5. Send updates to the lexicon to the backup server.
6. Turn to Step 1 of ‘Polling’ until manually killed by the user

## Backup Server Functions
**Startup**
1. Startup and listen for an incoming connection from the primary server.
2. Print that the primary server has connected.
3. Accept and apply updates received from the server to local copy of lexicon.

**On Primary Server Failure**
1. Notify the user that the primary server is not available.
2. Listen for incoming connections from clients.
3. Assume the responsibilities of 'Spell Check' and 'Polling' until manually killed by the user.
