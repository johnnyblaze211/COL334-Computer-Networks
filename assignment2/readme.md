# COL334 Assignment 2

### Dhairya Gupta, 2019CS50428

#### This is the implementation of a simple non-encrypted chat room using client-server architecture and TCP sockets.



1. Run server script:
```
python3 server.py
```
2. Run client script. Provide username(required), optional server IP(default is 127.0.0.1). Use --raw flag to print raw packet data on console:
```
python3 client.py -u <username> [-ip <address>] [--raw]
```

- Note: raw packet data is by default visible on server

3. Send messages to other clients by typing:``` @<recipient_username> <message block>```
4. To send broadcast message: ``` @ALL <message block> ``` 
5. To send Raw Packet Data from user input to sender socket: ``` @OVERRIDE <byte-string> ```


