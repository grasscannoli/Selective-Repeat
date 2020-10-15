import socket
import threading
import time
import sys
import random
import math

# Function to read input:
def init():
    debug = False; rcv_ip = 0; rcv_port = 0; seqfel = 0; pkt_len = 0; gen_rate = 0; mx_pkt = 0; win_siz = 0; mx_buf = 0
    arg = sys.argv[1:]
    if '-d' in arg:
        debug = True
    if '-s' in arg:
        rcv_ip = arg[arg.index('-s')+1]
    if '-p' in arg:
        rcv_port = int(arg[arg.index('-p')+1])
    if '-n' in arg:
        seqfel = int(arg[arg.index('-n')+1])
    if '-L' in arg:
        pkt_len = int(arg[arg.index('-L')+1])
    if '-R' in arg:
        gen_rate = int(arg[arg.index('-R')+1])
    if '-N' in arg:
        mx_pkt = int(arg[arg.index('-N')+1])
    if '-W' in arg:
        win_siz = int(arg[arg.index('-W')+1])
    if '-B' in arg:
        mx_buf = int(arg[arg.index('-B')+1])
    return debug, rcv_ip, rcv_port, seqfel, pkt_len, gen_rate, mx_pkt, win_siz, mx_buf

# Thread handle for ACK packets:
def ack_handle():
    # globals to be used:
    global s
    global qu
    global qlock
    global base 
    global nextseqnum
    global mx_pkt
    global tbl
    global rtt
    global unack
    global win_siz
    global ack
    global attempts_fl
    global debug
    global start_time
    global err_rate

    # Loop to handle ack:
    while True:
        if len(ack) >= mx_pkt or attempts_fl:
            break

        # wait for ack packets:
        data, _  = s.recvfrom(4096)
        try:
            seq = int(data.decode("utf-8"))        
        except:
            attempts_fl = True
            err_rate = float(data.decode("utf-8"))
            break
        qlock.acquire()

        # critical section:
        lst = [x[0] for x in qu]
        if seq in lst:

            #find the last index of lst with seq:
            for i in range(len(lst)):
                if lst[i] == seq:
                    qu.pop(i)[1].cancel()
        
        # update tbl and the rtt variable:
        tbl[seq] = (tbl[seq][0], time.time())
        rtt = (rtt*(seq)+tbl[seq][1]-tbl[seq][0])/(seq+1)        

        # update the local state variables, nextseqnum and base:
        if seq in unack:
            unack.pop(unack.index(seq))
        ack.add(seq)
        
        if len(unack) == 0:
            base = base + 1
        elif base == seq:
            base = unack[0]            

        # print('Ack recieved for:', seq, 'with rtt: ', tbl[seq][1]-tbl[seq][0], ' and base =', base)
        if debug:
            t = tbl[seq][0] - start_time
            RTT = tbl[seq][1]-tbl[seq][0]
            print(f'Seq {seq}: Time Generated: {math.floor(t*1000)}:{math.floor((t*1000-math.floor(t*1000))*1000)} RTT: {math.floor(RTT*1000)}:{math.floor((RTT*1000-math.floor(RTT*1000))*1000)} Number of Attempts: {num_attempts[seq]}')


        qlock.release()

# Thread handle for a packet timeout:
def timeout_handle(to_seq):
    # globals to be used:
    global qu 
    global qlock
    global base 
    global nextseqnum    
    global s    
    global rcv_ip
    global rcv_port
    global rtt
    global tbl
    global num_trans
    global attempts_fl

    qlock.acquire()

    # critical section:
    lst = [x[0] for x in qu]
    if to_seq in lst:
        msg = qu[lst.index(to_seq)][2]
       
        for i in range(len(lst)):
            if lst[i] == to_seq:
                qu.pop(i)[1].cancel()
        s.sendto(msg, (rcv_ip, rcv_port))
        tbl[to_seq] = (time.time(), -1)
        num_trans = num_trans + 1

        if to_seq in num_attempts.keys():
                num_attempts[to_seq] = num_attempts[to_seq] + 1
        else:
            num_attempts[to_seq] = 1
        if num_attempts[to_seq] > 10:
            attempts_fl = True                
        
        to_t = 0
        if to_seq > 9:
            to_t = threading.Timer(2*rtt, timeout_handle, (to_seq,))
        else:
            to_t = threading.Timer(0.1, timeout_handle, (to_seq,))
        to_t.start()
        qu.append((to_seq, to_t, msg))
    qlock.release()

# Thread handle to produce pkts into buffer:
def buf_handle():
    # globals to be used:
    global buf
    global block
    global gen_rate 
    global mx_pkt 
    global pkt_len
    global mx_buf
    global stop_fl
    global seqfel
    global attempts_fl

    sofargen = 0    
    while sofargen < 10000:
        if stop_fl or attempts_fl:
            break
        new_len = random.randint(40, pkt_len)
        msg = ''
        for _ in range(new_len-seqfel):
            msg = msg + '0'
        if len(buf) < mx_buf:
            block.acquire()

            #critical section:
            buf.append(msg)
            sofargen = sofargen + 1

            block.release()
            
        time.sleep((1/gen_rate))

    

# Main Program:
if __name__ == "__main__":
    # general initialization:
    debug, rcv_ip, rcv_port, seqfel, pkt_len, gen_rate, mx_pkt, win_siz, mx_buf = init()
    buf = []
    qu = []
    block = threading.Lock()
    qlock = threading.Lock()   
    base = 0; nextseqnum = 0     
    stop_fl = False
    tbl = {}
    rtt = 0.0
    unack = []
    ack = set()
    num_attempts = {}
    attempts_fl = False
    num_trans = 0
    start_time = time.time()
    err_rate = -1

    # socket initialization:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    server_addr = (s.getsockname()[0], 1234)
    s.close()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(server_addr)
    
    # thread initialization:
    ack_t = threading.Thread(target=ack_handle, args=())
    buf_t = threading.Thread(target=buf_handle, args=())
    ack_t.start()
    buf_t.start()

    # main thread:
    while len(ack) < mx_pkt:
        if nextseqnum - base < win_siz and len(buf) > 0 and nextseqnum < mx_pkt and (not attempts_fl):
            qlock.acquire()
            block.acquire()

            #critical area:
            #1. remove message, format:
            msg = buf.pop(0)
            msg = bytes(f'{nextseqnum:<{seqfel}}'+msg, "utf-8")

            #2. Create timeout thread, send message:
            if nextseqnum > 9:
                to_t = threading.Timer(2*rtt, timeout_handle, (nextseqnum,))
            else:
                to_t = threading.Timer(0.3, timeout_handle, (nextseqnum,))
            s.sendto(msg, (rcv_ip, rcv_port))

            #3. Add the seq_num and thread to qu after starting:
            to_t.start()
            qu.append((nextseqnum, to_t, msg))

            #4. Insert entry into the rtt table:
            if nextseqnum in tbl.keys() and tbl[nextseqnum][1] == -1:
                tbl[nextseqnum] = (time.time(), -1)
            elif not (nextseqnum in tbl.keys()):
                tbl[nextseqnum] = (time.time(), -1)

            if nextseqnum in num_attempts.keys():
                num_attempts[nextseqnum] = num_attempts[nextseqnum] + 1
            else:
                num_attempts[nextseqnum] = 1
            if num_attempts[nextseqnum] > 10:
                break                

            #5. Increment local state variable nextseqnum:            
            # print('Packet sent was:', nextseqnum)
            unack.append(nextseqnum)
            nextseqnum = (nextseqnum + 1)
            num_trans = num_trans + 1

            block.release()            
            qlock.release()
    stop_fl = True
    attempts_fl = True
    # print(rtt)
    raw_data, addr = s.recvfrom(4096)
    if err_rate == -1:
        err_rate = float(raw_data.decode("utf-8"))    
    for _ in range(len(qu)):
        qu.pop(0)[1].cancel()
    print(f'Output: PktRate = {gen_rate}, Drop prob = {err_rate}, Length = {pkt_len}, Retran Ratio = {num_trans/mx_pkt}, Avg RTT: {math.floor(rtt*1000)}:{math.floor((rtt*1000-math.floor(rtt*1000))*1000)}')


