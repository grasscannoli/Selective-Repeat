import socket
import time
from random import choices
import random
import sys
import math

# Function to take input:
def init():
    debug = False; rcv_port = 0; mx_pkt = 0; err = 0.
    arg = sys.argv[1:]
    if '-d' in arg:
        debug = True
    if '-p' in arg:
        rcv_port = int(arg[arg.index('-p')+1])
    if '-n' in arg:
        mx_pkt = int(arg[arg.index('-n')+1])
    if '-e' in arg:
        err = float(arg[arg.index('-e')+1])
    return debug, rcv_port, mx_pkt, err

if __name__ == "__main__":
    # general initialization:
    debug, rcv_port, mx_pkt, err = init()
    num_rcv = 0
    population = [0, 1]
    weights = [err, 1.-err]
    drop_fl = 0
    match_fl = 0
    cnt = 0
    saddr = 0
    num_attempts = {}
    start_time = time.time()

    # socket initialization:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    server_addr = (s.getsockname()[0], rcv_port)
    s.close()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(server_addr)

    # init pkt len:
    seq_len = 8

    while num_rcv < mx_pkt:
        drop_fl = 1
        match_fl = 0
        data, saddr = s.recvfrom(4096)
        seq = int(str(data.decode("utf-8"))[:seq_len])
        if seq in num_attempts.keys():
            num_attempts[seq] = num_attempts[seq]+1
        else:
            num_attempts[seq] = 1
        if num_attempts[seq] > 10:
            break
        data = bytes(f'{seq}', "utf-8")
        t = time.time()
        if random.random() > err:
            drop_fl = 0
            if seq == num_rcv:
                s.sendto(data, saddr)
                match_fl = 1
                num_rcv = num_rcv + 1
            else:
                data = bytes(f'{num_rcv-1}',"utf-8")
                s.sendto(data, saddr)
        cnt = cnt + 1
        if debug:
            t = time.time() - start_time
            print(f'Seq {seq}: Time Received: {math.floor(t*1000)}:{math.floor((t*1000-math.floor(t*1000))*1000)} Packet dropped: {drop_fl == 1}')
        # if match_fl == 1:
        #     print('expected:', num_rcv-1, 'recieved:', seq, 'dropped?:', drop_fl, 'matched?:', match_fl, 'num pkts rcved:', cnt)
        # else:
        #     print('expected:', num_rcv, 'recieved:', seq, 'dropped?:', drop_fl, 'matched?:', match_fl, 'num pkts rcved:', cnt)   
    s.sendto(bytes(f'{err}', "utf-8"), saddr)  
            
        