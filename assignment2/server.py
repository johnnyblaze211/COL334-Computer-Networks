import re
import socket
from _thread import *
import threading
import argparse
import warnings

client_to_recv_dict = {}        #hashtable for storing receiving sockets
MAX_LEN = 1024

#parse instruction received to server
def parse(msg, isRegistered, isSendingThread = False):
    
    if(re.match('^REGISTER TOSEND .*\n\n.*$', msg)):
        [msg, new_msg] = msg.split('\n\n', 1)
        user = msg[16:]
        if(user.isalnum()):
            return ('reg_send', [user]), new_msg
        else:
            return ('e100', [user]), new_msg
    elif(re.match('^REGISTER TORECV .*\n\n.*$', msg)):
        #print(list(msg))
        [msg, new_msg] = msg.split('\n\n', 1)
        #print((msg +', '+ new_msg))
        user = msg[16:]
        if(user.isalnum()):
            return ('reg_recv', [user]), new_msg
        else:
            return ('e100', [user]), new_msg
    elif(re.match('^SEND .*\nContent-length: [1-9][0-9]*\n\n.*$', msg)):
        
        [msg1, msg2] = msg.split('\n', 1)
        [msg2, msg3] = msg2.split('\n\n', 1)
        num = msg2[16:]
        #print(f'list(num): {list(num)}')
        if(not num.isnumeric()):
            return('e103', []), None
        num = int(num)
        if(len(msg3) < num):
            return ('e103', []), None
        else:
            content = msg3[:num]
            new_msg = msg3[num:]
            if not isRegistered:
                return ('e101', []), new_msg
            user = msg1[5:]
            if(not user.isalnum()):
                return ('e101', []), new_msg
            if user in client_to_recv_dict or user == 'ALL':
                return('forward', [user, content]), new_msg
            else:
                return ('e102', []), new_msg
        
    elif(re.match('^RECEIVED .*\n\n.*$', msg)):
        [msg, new_msg] = msg.split('\n\n', 1)
        if not isRegistered:
            return ('e101', []), new_msg
        user = msg[9:]
        return('receive', [user]), new_msg

    elif(re.match('^ERROR .*\n\n.*$', msg)):
        [msg, new_msg] = msg.split('\n\n')
        return('receive_error', []), new_msg
    
    else:
        return ('e103', []), None


#function for running thread
def client_thread_fn(sock_conn):
    e100 = b'ERROR 100 Malformed username\n\n'
    e101 = b'ERROR 101 No user registered\n\n'
    e102 = b'ERROR 102 Unable to send\n\n'
    e103 = b'ERROR 103 Header incomplete\n\n'
    isSendingThread = False
    isRegistered_to_send = False
    isRegistered_to_recv = False
    user = None
    new_msg = None
    while(not new_msg or new_msg == ''): new_msg = sock_conn.recv(MAX_LEN).decode()
    msg = new_msg
    while True:
        while new_msg == '' or new_msg is None:
            new_msg = sock_conn.recv(MAX_LEN).decode()
        msg = new_msg
        print(f'SOCK_SEND<{user}>##C2S: {msg.encode()}')
        (action, args_list), new_msg = parse(msg, isRegistered_to_send and (user in client_to_recv_dict))

        #action stores the function to be implemented for outgoing message from parse() method

        #Send REGISTERED TOSEND
        if action == 'reg_send':
            isRegistered_to_send = True
            if not user: user = args_list[0]
            str0 = 'REGISTERED TOSEND '+user+'\n\n'
            sock_conn.send(('REGISTERED TOSEND '+user+'\n\n').encode())
            print(f'SOCK_SEND<{user}>##S2C: {str0.encode()}')


        #SEND REGISTER TORECV message and close thread by return
        elif action == 'reg_recv' and not isRegistered_to_send:
            isRegistered_to_recv = True
            if not user: user = args_list[0]
            if not user in client_to_recv_dict:
                client_to_recv_dict[user] = sock_conn
            str0 = 'REGISTERED TORECV '+user+'\n\n'
            sock_conn.send(str0.encode())
            print(f'SOCK_SEND<{user}>##S2C: {str0.encode()}')
            return


        #SEND FORWARD MESSAGE and get acknowledgement from recipient. 
        #Closes reipient socket and removes from hashtable if unable to send message 
        elif action == 'forward':
            receiver = args_list[0]
            content = args_list[1]
            if receiver == 'ALL':
                sent_To_All = True
                bad_Receiver = None
                for rc in client_to_recv_dict:
                    if rc == user: continue
                    f_str = 'FORWARD '+ user +'\n' + 'Content-length: ' + str(len(content)) + '\n\n' + content
                    recv_sock = client_to_recv_dict[rc]
                    recv_sock.send((f_str).encode())
                    print(f'SOCK_RECV<{rc}>##S2C: {f_str.encode()}')
                    recv_sock.settimeout(5.)
                    try:
                        ack_rcv = recv_sock.recv(MAX_LEN).decode()
                        print(f'SOCK_RECV<{rc}>##C2S: {ack_rcv.encode()}')
                        (a1, l1), _ = parse(ack_rcv, True)
                        if a1 == 'receive':
                            continue
                        else:
                            sent_To_All = False
                            bad_Receiver = rc
                            break
                    except socket.timeout:
                        bad_Receiver = rc
                        sent_To_All = False
                        break
                if sent_To_All:
                    str2 = 'SEND ' + receiver + '\n\n'
                    sock_conn.send(str2.encode())
                    print(f'SOCK_SEND<{user}>##S2C: {str2.encode()}')
                else:
                    sock_conn.send(e102)
                    print(f'SOCK_SEND<{user}>##S2C: {e102}')
                    bad_sock = client_to_recv_dict[bad_Receiver]
                    client_to_recv_dict.pop(bad_Receiver)
                    bad_sock.close()
                    print(f'SOCK_RECV<{bad_Receiver}> Closed')
            else:
                recv_sock = client_to_recv_dict[receiver]
                f_str = 'FORWARD '+ user +'\n' + 'Content-length: ' + str(len(content)) + '\n\n' + content
                #print(f_str)
                recv_sock.send((f_str).encode())
                print(f'SOCK_RECV<{receiver}>##S2C: {f_str.encode()}')
                recv_sock.settimeout(5.)
                acked = True
                try:
                    ack_rcv = recv_sock.recv(MAX_LEN).decode()
                    print(f'SOCK_RECV<{receiver}>##C2S: {ack_rcv.encode()}')
                    #print(ack_rcv)
                    (a1, l1), _ = parse(ack_rcv, True)
                    if a1 == 'receive':
                        str2 = 'SEND ' + receiver+ '\n\n'
                        sock_conn.send(str2.encode())
                        print(f'SOCK_SEND<{user}>##S2C: {str2.encode()}')
                    else:
                        sock_conn.send(e102)
                        print(f'SOCK_SEND<{user}>##S2C: {e102}')
                        client_to_recv_dict.pop(receiver)
                        recv_sock.close()
                        print(f'SOCK_RECV<{receiver}> Closed')
                        
                except socket.timeout as err:
                    acked = False
                    print(err)
                    sock_conn.send(e102)
                    print(f'SOCK_SEND<{user}>##S2C: {e102}')
                    client_to_recv_dict.pop(receiver)
                    recv_sock.close()
                    print(f'SOCK_RECV<{receiver}> Closed')
                    
                #recv_sock.settimeout(None)

        #Send Error messages to client
        elif action == 'e100':
            sock_conn.send(e100)
            print(f'SOCK_SEND<{user}>##S2C: {e100}')
        elif action == 'e101':
            sock_conn.send(e101)
            print(f'SOCK_SEND<{user}>##S2C: {e101}')
        elif action == 'e102':
            sock_conn.send(e102)
            print(f'SOCK_SEND<{user}>##S2C: {e102}')
        elif action == 'e103' or action == 'receive_error':
            sock_conn.send(e103)
            print(f'SOCK_SEND<{user}>##S2C: {e103}')
            sock_conn.close()
            print(f'SOCK_SEND<{user}> Closed')
            sock_recv = client_to_recv_dict[user]
            client_to_recv_dict.pop(user)
            sock_recv.close()
            print(f'SOCK_SEND<{user} Closed>')
            return
        else:
            sock_conn.send(e103)
            print(f'SOCK_SEND<{user}>##S2C: {e103}')
            sock_conn.close()
            print(f'SOCK_SEND<{user}> Closed')
            sock_recv = client_to_recv_dict[user]
            client_to_recv_dict.pop(user)
            sock_recv.close()
            print(f'SOCK_SEND<{user} Closed>')
            return








    

if __name__ == '__main__':
    #arbitrary chosen port value
    #client must connect to same port
    port = 56201

    #initialize and bind socket
    sock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_server.bind(('127.0.0.1', port))

    #Can increase limit if more users expected
    sock_server.listen(100)

    #ThreadList so that threads are not removed from scope
    threads = []

    while(True):

        #accept connection and start thread
        sock_conn, client_addr = sock_server.accept()
        
        thread1 = threading.Thread(target=client_thread_fn, args = (sock_conn, ))
        thread1.start()
        threads.append(thread1)

    


        




        




