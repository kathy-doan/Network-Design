# Design File

---

### Title and Authors
* Phase 3
* Benjamin Dearden
* Michael Smith
* Peter Dingue
* Kathy Doan

### Purpose of The Phase
The purpose of this phase is to implement RDT 3.0 by modifying phase 2's <br>
RDT 2.2 by desensitizing the sender to irrelevant ACK messages and using timer's <br>
to trigger retransmission. 

### Code Explanation

Client (v3_client.py): This script reads a file and splits it into packets, then <br> 
implements a stop and wait arq with sequence numbers. The client is desensitized <br>
to irrelevant ACK messages and relies on timeout to trigger packet retransmission. <br>
The client also simulates ACK packet bit error. 

Server (v3_server.py): This script listens for packets on a UDP socket. The packets <br>
are validated using checksum and sequence number, the server implements data packet loss <br>
by ignoring packets and sending previous ACK. The server also simulates Data packet bit error. <br>

Helper Functions (v3_udp_helpers.py): This script contains the useful functionality required <br>
by the client and server scripts. 

![alt text](./plots/plot_1.png)
Pictured above is the completion time graph for all 5 simulations 
the code runs. The Data loss line <br> shows faster execution time
than the Data bit error line. This is likely due to data bit error 
retransmitting packets that still have bit errors. Whereas a lost packet 
can be retransmitted <br> after timing out and be successfully recieved 
with no data errors. 

![alt text](./plots/Retransmissions.png)
Pictured above is the average retransmissions for each error mode.


![alt text](./plots/Throughput.png)





