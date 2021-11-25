__________________________________________________________________________________________________________________________________________________________
FILE LISTS
- client.py: TCP client side that sends segments with pipelining and timeout mechanism
- server.py: TCP server side that receives inorder segments without buffering mechanism
- segment_processor.py: Assemble and disassemble segments, and detect bit errors
- source_file.txt: Stores the source Unicode texts to be sent by the client
- dest_file.txt: Stores the Unicode texts received and then parsed by the server
- client_log.txt: Stores the client side action during transmission
- server_log.txt: Stores the server side action during transmission
__________________________________________________________________________________________________________________________________________________________
COMMAND RUNS GUIDELINE
- WARNINGS
  1. To make sure the program can run successfully, please run the command lines indicated in the "COMMAND"
  2. My program runs locally, meaning using localhost
  3. Please make sure to use python3 to run the program, some syntax are specific in python 3, I use python 3.7 particularly
- STEP1: boot up the NEWUDPL server
  FORMAT: ./newudpl [-i source_host:port/*] [-o dest_host:port/*] [-L random_pack_loss_rate] [-B bit_error_rate] [-O out_of_order_rate] [-d delay]
  COMMAND: ./newudpl -i 'localhost':'*' -o 'localhost':8000 -L 10 -B 10 -O 10 -d 1
- STEP2: boot up the TCP server
  FORMAT: python3 [tcpserver] [file] [listening_port] [address_for_acks] [port_for_acks]
  COMMAND: python3 server.py dest_file.txt 8000 localhost 9000
- STEP3: boot up the TCP client
  FORMAT: python3 [tcpclient] [file] [address_of_udpl] [port_number_of_udpl] [windowsize] [ack_port_number]
  COMMAND: python3 client.py source_file.txt localhost 41192 1536 9000
  EXTRA: window size is measured in byte, I set my MSS as 512 internally, therefore, the window size in count is approximately 3
__________________________________________________________________________________________________________________________________________________________
POTENTIAL BUGS AND FEATURES
- BUGS
  If the source_file.txt is empty, I'm not so sure if the system can handle it correctly without throwing exception. Since we need to at least send
  something to the server in our simulation, it's legit to assume that the source text won't be empty. It's just a potential problems I want to mention.
  The message transmission might take some time base on different values of factors, I'm not sure if this is caused by the MSS, or the loss rate, bit
  error rate, out of order rate, and delay we set up in the NEWUDPL, or something wrong with my algorithm, or something else, or the aggregation effect
  of all them. It's hard to figure out and I just pick the ideal values to make sure the transmission runs relatively faster. So don't change the values I
  set up above in the commands, I mean at least I've tested those could run relatively at a decent speed.
- FEATURES
  I've added some subtle features to help improve the user experience, such as the client_log.txt and server_log.txt for recording the client and server
  "SEND", "RESEND", "RECEIVE" actions such that users can basically construct and visualize the client-server interactions with those information. Besides,
  I also print out the received number of ACK as client runs, this feature kind of visualize the communication process and let the user knows which stage
  he is on, since it might take some time for the program to finish. Lastly, my server will automatically shut down after one communication finished, this
  is not the case in real life, I do it because all we want it's just a simulation.
__________________________________________________________________________________________________________________________________________________________