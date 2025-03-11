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

![alt text](./plots/example_plots/CompletionRun1.png)
Pictured above is the completion time graph for all 5 simulations 
the code runs. The Data loss line <br> shows faster execution time
than the Data bit error line. This is likely due to data bit error 
retransmitting packets that still have bit errors. Whereas a lost packet 
can be retransmitted <br> after timing out and be successfully recieved 
with no data errors. Another factor that may have affect <br>
the shorter completion times for Data loss and not Data bit error are the 
recovery methods for when <br> a received packet is corrupted is the method
of recovery used within the code. The receiver needs to <br> check a packet 
to verify it contents are not corrupted whereas it does not need to check <br>
anything when it fails to receive a packet. In that case the sender never 
receives an ACK and <br> proceeds to resend the packet which can lead to packet 
loss taking less time to complete than <br> processing bit errors.

![alt text](./plots/example_plots/RetransmissionRun1.png)
Pictured above is the average retransmissions for each error mode.


![alt text](./plots/example_plots/ThroughputRun1.png)
Pictured above is the throughput for each error mode in bytes per second
this graph correlates <br> with the first graph displaying completion times. 
The lines have inverse relations. The faster the completion time the less the
throughput declines as the error rate increases. 

## Discussion/Analysis
The code used to generate the previously displayed plots did not have a specified seed value.
<br> With each run comes some variance in the graphed plots. The source of this variance is not <br>
exactly clear. We have implemented a static seed value of 123 to generate two more sets of plots <br>
and the variance between the two runs is still visible. Shown below are the plotted results.

![alt text](./plots/example_plots/CompletionSeeded1.png)
Run 1 Completion time above.
![alt text](./plots/example_plots/RetransmissionSeeded1.png)
Run 1 Retransmission average above.
![alt text](./plots/example_plots/ThroughputSeeded1.png)
Run 1 Throughput in bytes per second above.
![alt text](./plots/example_plots/CompletionSeeded2.png)
Run 2 Completion time above.
![alt text](./plots/example_plots/RetransmissionSeeded1.png)
Run 2 Retransmission average above.
![alt text](./plots/example_plots/ThroughputSeeded2.png)
Run 2 Throughput in bytes per second above.

The one thing that remains consistent across these plotted graphs 
is the average number <br> of retransmissions. The completion 
time graph has difficult to explain anomalies in some of the <br>
modes where a higher percent error can result in a faster completion 
time. When the expected <br> behavior would be a slower completion time
as the error rate increases. We believe this may <br> be caused by 
the corruption implementations. Another potential factor causing this variance <br>
may be the machine the code is running on and the environmental factors that 
are not controllable. 




