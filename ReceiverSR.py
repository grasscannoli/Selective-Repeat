import socket
import time
from random import choices
import random
import sys
import math

# Function to take input:
def init():
    debug = False; rcv_port = 0; mx_pkt = 0; seqfel = 0; win_siz = 0; mx_buf = 0; err = 0.
    arg = sys.argv[1:]
    if '-d' in arg:
        debug = True
    if '-p' in arg:
        rcv_port = int(arg[arg.index('-p')+1])
    if '-N' in arg:
        mx_pkt = int(arg[arg.index('-N')+1])
    if '-n' in arg:
        seqfel = int(arg[arg.index('-n')+1])
    if '-W' in arg:
        win_siz = int(arg[arg.index('-W')+1])
    if '-B' in arg:
        mx_buf = int(arg[arg.index('-B')+1])
    if '-e' in arg:
        err = float(arg[arg.index('-e')+1])
    return debug, rcv_port, mx_pkt, seqfel, win_siz, mx_buf, err

if __name__ == "__main__":
    # general initialization:
    debug, rcv_port, mx_pkt, seqfel, win_siz, mx_buf, err = init()
    num_rcv = 0
    drop_fl = 0
    match_fl = 0
    pkt_tbl = dict([(seq, False) for seq in range(mx_pkt)])
    base = 0
    ack = set()
    start_time = time.time()
    num_attempts = {}

    # socket initialization:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    server_addr = (s.getsockname()[0], rcv_port)
    s.close()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(server_addr)
    cnt = 0
    saddr = 0
    while len(ack) < mx_pkt:
        drop_fl = 1
        match_fl = 0
        # print("before rcv")
        data, saddr = s.recvfrom(4096)
        # print('after rcv')
        seq = int(str(data.decode("utf-8")[:seqfel]))
        data = bytes(f'{seq}', "utf-8")
        # seq = int(data.decode("utf-8"))
        if random.random() > err:
            drop_fl = 0
            if seq >= base and seq < min(mx_pkt, base + win_siz):
                match_fl = 1
                pkt_tbl[seq] = True
                s.sendto(data, saddr)
                if seq == base:
                    prev = base
                    for rcved in range(min(base+win_siz, mx_pkt)):
                        if not pkt_tbl[rcved]:
                            base = rcved
                            break
                    if prev == base:
                        base = base + 1
                num_rcv = num_rcv + 1
                ack.add(seq)
            elif seq >= max(0, base-win_siz) and seq < base:
                s.sendto(data, saddr)
        if seq in num_attempts.keys():
            num_attempts[seq] = num_attempts[seq] + 1
        else:
            num_attempts[seq] = 1
        if num_attempts[seq] > 10:
            break
            
        cnt = cnt + 1
        # print('recieved:', seq, 'dropped?:', drop_fl, 'matched?:', match_fl, 'num pkts correctly rcved:', num_rcv, 'total rcved', cnt, 'base =', base)
        if debug:
            t = time.time() - start_time
            print(f'Seq {seq}: Time Received: {math.floor(t*1000)}:{math.floor((t*1000-math.floor(t*1000))*1000)} Packet dropped: {drop_fl == 1}')
    s.sendto(bytes(f'{err}', "utf-8"), saddr)
            
        