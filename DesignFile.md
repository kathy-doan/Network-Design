# Design File

---

### Title and Authors
* Phase 2
* Benjamin Dearden
* Micheal
* Peter
* Kathy

### Purpose of The Phase
This phase's purpose is to implement rdt 2.2 on top of phase 1 rdt 1.0. The protocol provides reliable data transfer over an unreliable network with simulated errors. <br>



### Code Explanation
Client (v2_client.py): This script reads/sends a file in packets and implements error handling for ack bit errors.

Server (v2_server.py): This script recieves/reocnstructs the files and implements error handling for data pakcet bit erros.

Helper functions (v2_udp_helps.py): This script handles checksum computation and packet creation and simulates bit errors and packet loss.

Test harness (harness.py): This script automates the testing and plots completion times vs error rates.

rdt 2.2: This reliable data transfer 2.2 uses sequence numbers to detect duplicate packets and implements a checksum verification to detect corruption. It is using nak free retransmission meaning its only sending packets when needed.
