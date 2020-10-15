import socket
import threading
import time
import sys
import math

# Function to read input:
def init():
    debug = False; rcv_ip = 0; rcv_port = 0; pkt_len = 0; gen_rate = 0; mx_pkt = 0; win_siz = 0; mx_buf = 0
    arg = sys.argv[1:]
    if '-d' in arg:
        debug = True
    if '-s' in arg:
        rcv_ip = arg[arg.index('-s')+1]
    if '-p' in arg:
        rcv_port = int(arg[arg.index('-p')+1])
    if '-l' in arg:
        pkt_len = int(arg[arg.index('-l')+1])
    if '-r' in arg:
        gen_rate = int(arg[arg.index('-r')+1])
    if '-n' in arg:
        mx_pkt = int(arg[arg.index('-n')+1])
    if '-w' in arg:
        win_siz = int(arg[arg.index('-w')+1])
    if '-b' in arg:
        mx_buf = int(arg[arg.index('-b')+1])
    return debug, rcv_ip, rcv_port, pkt_len, gen_rate, mx_pkt, win_siz, mx_buf

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
    global num_attempts
    global debug
    global start_time
    global attempts_fl

    # Loop to handle ack:
    while True:
        if base == mx_pkt or attempts_fl:
            break

        # wait for ack packets:
        data, _  = s.recvfrom(4096)
        t = time.time()
        seq = int(data.decode("utf-8"))        
        qlock.acquire()

        # update tbl and the rtt variable:
        tbl[seq] = (tbl[seq][0], t)
        rtt = (rtt*(seq)+tbl[seq][1]-tbl[seq][0])/(seq+1)

        # critical section:
        lst = [x[0] for x in qu]
        if seq in lst:
            idx = 0

            #find the last index of lst with seq:
            for i in range(len(lst)):
                if lst[i] == seq:
                    idx = i

            #pop all the elements till this element:        
            for i in range(idx+1):
                qu.pop(0)[1].cancel()
        
        #print('Ack recieved for:', seq, 'with rtt: ', tbl[seq][1]-tbl[seq][0])
        if debug:
            t = tbl[seq][0] - start_time
            RTT = tbl[seq][1]-tbl[seq][0]
            print(f'Seq {seq}: Time Generated: {math.floor(t*1000)}:{math.floor((t*1000-math.floor(t*1000))*1000)} RTT: {math.floor(RTT*1000)}:{math.floor((RTT*1000-math.floor(RTT*1000))*1000)} Number of Attempts: {num_attempts[seq]}')

        # update the local state variables nextseqnum and base:
        base = seq + 1
        if nextseqnum < base:
            nextseqnum = base

        qlock.release()

# Thread handle for a packet timeout:
def timeout_handle(to_seq):
    # globals to be used:
    global qu 
    global qlock
    global base 
    global nextseqnum    

    qlock.acquire()

    # critical section:
    lst = [x[0] for x in qu]
    if to_seq in lst:
        #print('timed out for:', to_seq)
        qu = []
        nextseqnum = base

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

    sofargen = 0
    message = ''
    for _ in range(pkt_len-8):
        message = message + '0'
    while sofargen < 10000:
        if stop_fl or attempts_fl:
            break
        if len(buf) < mx_buf:
            block.acquire()

            #critical section:
            msg = message
            buf.append(msg)
            sofargen = sofargen + 1

            block.release()
            
        time.sleep((1/gen_rate))

    

# Main Program:
if __name__ == "__main__":
    # general initialization:
    debug, rcv_ip, rcv_port, pkt_len, gen_rate, mx_pkt, win_size, mx_buf = init()
    buf = []
    qu = []
    block = threading.Lock()
    qlock = threading.Lock()   
    base = 0; nextseqnum = 0     
    stop_fl = False
    tbl = {}
    rtt = 0.0
    num_trans = 0
    num_attempts = {}
    start_time = time.time()
    attempts_fl = False

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
    while base < mx_pkt:
        if nextseqnum - base < win_size and len(buf) > 0 and nextseqnum < mx_pkt:
            qlock.acquire()
            block.acquire()

            #critical area:
            #1. remove message, format:
            msg = buf.pop(0)
            msg = bytes(f'{nextseqnum:<8}'+msg, "utf-8")

            #2. Create timeout thread, send message:
            if nextseqnum > 9:
                to_t = threading.Timer(2*rtt, timeout_handle, (nextseqnum,))
            else:
                to_t = threading.Timer(0.1, timeout_handle, (nextseqnum,))
            s.sendto(msg, (rcv_ip, rcv_port))
            t = time.time()

            #3. Add the seq_num and thread to qu after starting:
            to_t.start()
            qu.append((nextseqnum, to_t))

            #4. Insert entry into the rtt table:
            if nextseqnum in tbl.keys() and tbl[nextseqnum][1] == -1:
                tbl[nextseqnum] = (t, -1)
            elif not (nextseqnum in tbl.keys()):
                tbl[nextseqnum] = (t, -1)
            
            if nextseqnum in num_attempts.keys():
                num_attempts[nextseqnum] = num_attempts[nextseqnum] + 1
            else:
                num_attempts[nextseqnum] = 1
            if num_attempts[nextseqnum] > 10:
                attempts_fl = True
                break

            #5. Increment local state variable nextseqnum:
            #print('Packet sent was:', nextseqnum)
            nextseqnum = nextseqnum + 1
            num_trans = num_trans + 1

            block.release()            
            qlock.release()
    stop_fl = True
    raw_data, addr = s.recvfrom(4096)
    err_rate = float(raw_data.decode("utf-8"))
    print(f'Output: PktRate = {gen_rate}, Drop prob = {err_rate}, Length = {pkt_len}, Retran Ratio = {num_trans/mx_pkt}, Avg RTT: {math.floor(rtt*1000)}:{math.floor((rtt*1000-math.floor(rtt*1000))*1000)}')
