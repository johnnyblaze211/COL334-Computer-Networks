import re
import socket
from _thread import *
import threading
import argparse
import time


MAX_LEN = 1024

received_response = True

#returns tokens username, message block from input string
def parse_input_msg(msg):
    msg = msg.strip()
    if not re.match('^@.+ .+$', msg):
        return False, None
    else:
        [user, content] = msg[1:].split(' ', 1)
        if user == '':
            return False, None
        else:
            content.lstrip(' ')
            return True, [user, content]

#parse FORWARD message on TORECV thread to determine acknowledgement
def parse_torecv(msg):
    if(re.match('^FORWARD .*\nContent-length: .*\n\n.*$', msg)):
        #print(msg)
        msg2 = msg[8:]
        [user, msg2] = msg2.split('\n', 1)
        if user == '':
            return 'e103', None
        else:
            if(msg2.startswith('Content-length: ')):
                msg2 = msg2[16:]
                [num, msg2] = msg2.split('\n\n', 1)
                if num.isnumeric():
                    n = int(num)
                    if(len(msg2)>=n):
                        content = msg2[:n]
                        new_msg = msg2[n:]
                        return 'received', [user, content, new_msg]

                    else:
                        return 'e103', None

                else: return 'e103', None

                
            else:
                return 'e103', None
    else:
        return 'e103', None
    
# function running on TOSEND thread
def sender(sock_send, user, raw = False):
    e100 = b'ERROR 100 Malformed username\n\n'
    e101 = b'ERROR 101 No user registered\n\n'
    e102 = b'ERROR 102 Unable to send\n\n'
    e103 = b'ERROR 103 Header incomplete\n\n'
    while True:
        #time.sleep(1)
        str1 = input()
        bool1, arr = parse_input_msg(str1)
        if bool1 and arr[0] != 'OVERRIDE':

            str0 = 'SEND ' + arr[0] + '\nContent-length: ' + str(len(arr[1])) + '\n\n' + arr[1]
            if(raw): print(f'SOCK_SEND##C2S: {str0.encode()}')
            sock_send.send(str0.encode())
            if(raw):print('SOCK_SEND##C2S: Sent Successfully')
            ack1 = sock_send.recv(1024).decode()
            #print(f'sender expected ack: {list(str_exp)}')
            #print(f'sender ack: {list(ack1)}')
            if raw: print(f'SOCK_SEND##S2C: {ack1.encode()}')
            if ack1 == 'SEND '+arr[0]+'\n\n':
                print('Sent')
            elif ack1 == e103.decode():
                print('!!Server: ' + ack1.rstrip('\n\n'))
                print('Closing Connection...')
                sock_send.close()
                print('Closed')
                return
            elif ack1 == e102.decode():
                print('Unable To Send')
            else:
                if not raw: print(f'!!Server: {ack1}')
                
                #if raw: print(f'Unrecognized ack: {ack1.encode()}')
        
        #Case when @OVERRIDE is used
        elif bool1 and arr[0] == 'OVERRIDE':
            ins = arr[1]
            s = list(ins)
            for i in range(len(s)):
                if((s[i] == '\\' and i+1<len(s)) and s[i+1] == 'n'):
                    s[i+1] = '\n'

            s1 = [char1 for char1 in s if char1!='\\']
            ins = ''.join(s1)
            if raw: print(f'SOCK_SEND##C2S: {ins.encode()}')
            sock_send.send(ins.encode())
            if raw: print(f'SOCK_SEND##C2S: Sent Successfully')
            response = sock_send.recv(MAX_LEN)
            if raw: print(f'SOCK_SEND##S2C: {response}')
            
        else:
            print('Invalid message format')


            
        
#function running on TORECV thread 
def receiver(sock_recv, raw = False):
    e100 = b'ERROR 100 Malformed username\n\n'
    e101 = b'ERROR 101 No user registered\n\n'
    e102 = b'ERROR 102 Unable to send\n\n'
    e103 = b'ERROR 103 Header incomplete\n\n'
    while True:
        msg = None
        while not msg: msg = sock_recv.recv(1024).decode()
        if raw: print(f'SOCK_RECV##S2C: {msg.encode()}')
        action, arr = parse_torecv(msg)
        if not arr:
            sock_recv.send(e103)
            sock_recv.close()
            return
        else:
            str1 = 'RECEIVED '+arr[0]+'\n\n'
            if raw: print(f'SOCK_RECV##C2S: {str1.encode()}')
            sock_recv.send(str1.encode())
            if raw: print('SOCK_RECV##C2S: Sent Successfully')

            print(arr[0]+': '+arr[1])

            msg = arr[2]



if __name__ == '__main__':

    #Command line argparse
    parser = argparse.ArgumentParser(description='Client application')
    parser.add_argument('--user', '-u', metavar = '<username>', help = 'username for client', required = True)
    parser.add_argument('--server', '-ip', metavar = '<IP_address>', help = 'server IP address')
    parser.add_argument('--raw', '-r', help = 'view raw packets sent and received', action='store_true')
    args = parser.parse_args()

    raw = args.raw
    username = args.user
    server_ip = '127.0.0.1'
    if args.server:
        server_ip = args.server

    #initialize sockets
    port = 56201            #Can change if server port changes
    sock_tosend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_tosend.connect((server_ip, port))

    sock_torecv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_torecv.connect((server_ip, port))

    '''##additional
    str0 = 'SEND '+username+'\nContent-length: 3\n\nBlue'
    print(f'SOCK_SEND##C2S: {str0.encode()}')
    sock_tosend.send(str0.encode())
    print(f'SOCK_SEND##C2S: Sent Successfully')

    r1 = sock_tosend.recv(1024).decode()
    print(f'SOCK_SEND##S2C: {r1.encode()}')'''




    #Client TOSEND socket registration
    str0 = 'REGISTER TOSEND '+username+'\n\n'
    if(raw): print(f'SOCK_SEND##C2S: {str0.encode()}')
    sock_tosend.send(str0.encode())
    if raw: print(f'SOCK_SEND##C2S: Sent Successfully')

    r1 = sock_tosend.recv(1024).decode()
    if raw: print(f'SOCK_SEND##S2C: {r1.encode()}')
    while r1 != 'REGISTERED TOSEND '+username+'\n\n':
        if r1 == 'ERROR 100 Malformed username\n\n':
            username = input('Username not valid. Re-Enter valid username: ')
        
        str0 = 'REGISTER TOSEND '+username+'\n\n'
        if raw: print(f'SOCK_SEND##C2S: {str0.encode()}')
        sock_tosend.send(str0.encode())
        if raw: print(f'SOCK_SEND##C2S: Sent Successfully')


        r1 = sock_tosend.recv(1024).decode()
        if raw: print(f'SOCK_SEND##S2C: {r1.encode()}')

    #Client TORECV socket registration
    str1 = 'REGISTER TORECV '+username+'\n\n'
    if raw: print(f'SOCK_RECV##C2S: {str1.encode()}')
    sock_torecv.send(str1.encode())
    if raw: print(f'SOCK_RECV##C2S: Sent Successfully')


    r2 = sock_torecv.recv(1024).decode()
    if raw: print(f'SOCK_RECV##S2C: {r2.encode()}')

    while r2 != 'REGISTERED TORECV '+username+'\n\n':
        str1 = 'REGISTER TORECV '+username+'\n\n'
        if raw: print(f'SOCK_RECV##C2S: {str1.encode()}')
        sock_torecv.send(str1.encode())
        if raw: print(f'SOCK_RECV##C2S: Sent Successfully')


        r2 = sock_torecv.recv(1024).decode()
        if raw: print(f'SOCK_RECV##S2C: {r2.encode()}')

    #Initializing threads
    t1 = threading.Thread(target = sender, args = (sock_tosend, username, raw))
    t2 = threading.Thread(target = receiver, args = (sock_torecv, raw))
    t1.start()
    t2.start()
    #start_new_thread(sender, (sock_tosend, username))
    #start_new_thread(receiver, (sock_torecv, ))









