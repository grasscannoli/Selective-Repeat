# Selective-Repeat and Go Back-N
RDT using Selective Repeat and Go Back-N in Python.

Assignment under Prof. Manikantan Srinivasan

#############################################################################

                    README Networks Assignment 2: CS17B045

#############################################################################

**********************************GBN****************************************

1) The Sender and Receiver Files are:
    1.1) SenderGBN.py
    1.2) ReceiverGBN.py
2) To run the programs, one must have two machines ideally, and both connected to the same internet
    connection. 
3) Since the scripts are in python there is no Makefile
4) Both the systems must have python 3.7 as the default python version
5) The user must run the command 'ifconfig'(linux)/'ipconfig'(windows) on the Receiver Machine and
    retrieve the IP Address of the correct Network Adapter.
6) The user must use this IP while invoking the Sender Program.
7) The following commands can be used to invoke the two programs on their respective machines:
    7.1)python SenderGBN.py -d -s <IP Address Receiver> -p 1235 -l 256 -r 300 -n 100 -w 10 -b 15
    7.2)python ReceiverGBN.py -d -p 1235 -n 100 -e 1e-5
8) The Flags are invoked according to the Assignment specifications.

***********************************SR****************************************

1) The Sender and Receiver Files are:
    1.1) SenderSR.py
    1.2) ReceiverSR.py
2) To run the programs, one must have two machines ideally, and both connected to the same internet
    connection.
3) Since the scripts are in python there is no Makefile
4) Both the systems must have python 3.7 as the default python version
5) The user must run the command 'ifconfig'(linux)/'ipconfig'(windows) on the Receiver Machine and
    retrieve the IP Address of the correct Network Adapter.
6) The user must use this IP while invoking the Sender Program.
7) The following commands can be used to invoke the two programs on their respective machines:
    7.1)python SenderSR.py -d -s <IP Address Receiver> -p 1235 -n 10 -L 1024 -R 300 -N 100 -W 10 -B 15
    7.2)python ReceiverSR.py -d -p 1235 -N 100 -n 10 -W 10 -B 15 -e 1e-7
8) The Flags are invoked according to the Assignment specifications. Note that the only difference is -n flag here takes
    the argument as the number of digits of sequence number and not bits of sequence number
