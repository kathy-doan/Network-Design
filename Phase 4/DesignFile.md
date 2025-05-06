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
The plot above shows the performance of Go-Back-N protocol with sliding window of 10. The ACK bit loss and ACK loss result 
in the same performance times due to the simulated loss method. Data bit error and Data loss are similar in performance times but not as close together as 
ACK errors. 
![alt text](./plots/retransverror3trials.png)
This plot shows the retransmissions for each mode. Modes 1, 2, and 4 do not trigger retransmission. For mode one
this is expected, but for modes 2 and 4 with ACK loss the reason there is no triggered retransmission
is that Go-Back-N uses cumulative ACK. An ACK can go missing or get corrupted, as long as an ACK comes in after 
before the timer expires it will continue transmitting fresh packets. 
![alt text](./plots/throughputverror3trial.png)
Here we see the throughput for each mode, as error increases the throughput slows down for modes 
<br> 2-5. 


Extra Credit:
![alt text](./pics/chart1_protocol_vs_loss.png)
![alt text](./pics/chart2_timeout_optimization.png)
![alt text](./pics/chart3_window_optimization.png)
![alt text](./pics/chart4_protocol_comparison.png)
