# Design File

---

### Title and Authors
* Phase 4
* Benjamin Dearden
* Michael Smith
* Peter Dingue
* Kathy Doan

### Purpose of The Phase
The purpose of this phase is to implement Go-Back-N protocol over an <br>
unreliable UDP channel. 

### Code Explanation
The python code for this project simulates Go-Back-N protocol by using a sliding window and <br>
cumulative ACKs to send packets from client to server. The server will send ACKs back to the client <br>
some of which can get lost. When an ACK is sent a timer begins and if an ACK is not received <br>
before a timeout an exception will be thrown causing all packets within the current window to be <br>
retransmitted. If an ACK is received after missing a few before the timer times out the previously <br>
missed ACKs are ignored because the ACKs are cumulative. All ACKs prior to the current one are <br>
recognized and the sender can continue to transmit the following packets. 
![alt text](./pics/mode3mode5.png)
Above is the code that simulates data errors in the code to cause a packet to become corrupted at <br>
the sender.
![alt text](./pics/mode2mode4.png)
Above is the code the simulates ACK errors to cause a packet ACK to get lost. An ACK bit error or <br>
ACK loss the result is the same. The ACK is not correct and if a higher ACK is not recieved before <br> 
timeout a retransmission will occur. The simulated error results in the received ACK being lower than <br>
the expected ACK so that it does not result in a higher ACK clearing previously lost ACKs due to <br>
cumulative acknowledgement. These modes use a pseudo delay to simulate the extra processing required 
to recover from ACK loss. Which in Go-Back-N is very little thanks to cumulative ACK.

![alt text](./plots/completionvError3trial.png)
![alt text](./plots/retransverror3trials.png)
![alt text](./plots/throughputverror3trial.png)
