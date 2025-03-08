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

