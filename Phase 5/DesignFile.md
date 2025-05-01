# Design File

---

### Title and Authors
* Phase 5
* Benjamin Dearden
* Michael Smith
* Peter Dingue
* Kathy Doan

### Purpose of The Phase
The purpose of this phase is to implement a simplified version of TCP using unreliable <br>
UDP sockets. The features implemented include: Connection setup and teardown, checksum implementation, <br>
Reliable data transfer (RDT), Timeout estimation and RTT calculation, and congestion control using standard <br>
TCP strategies. 

### Code Explanation

CHART 1
![alt text](./plots/completion_vs_errorrate.png)
In the image above the completion time vs error rate is shown for each mode. The almost unaffected <br>
modes 2 and 4 maintain speed close to that of no error because TCP uses cumulative ACK. A lost or corrupted <br>
ACK does not do much to reduce the completion time of the program. The spikes in the graph across the 5 <br>
modes, particularly 3 and 5 are likely that way because the dynamic window sizing and congestion <br>
control protocols are more efficient at specific error rates.

CHART 2
![alt text](./plots/completion_vs_timeout.png)
In this plot we see the performance effect on completion time based on timeout value with a fixed error rate <br>
of 20%. We see it has its best performance with a timeout around 30ms and 70 ms. Other timeout values <br> 
result in slight increases in completion time. 

CHART 3
![alt text](./plots/completion_vs_windowsize.png)
In this plot we see the performance impact of window size on completion time. It shows a generally <br>
downward trend, the bigger the window size, the faster the completion time. 

The next 5 plots display for each mode the change over time in the congestion window size at a fixed 20% error<br>
![alt text](./plots/cwnd_vs_time_mode1_error20.png)
![alt text](./plots/cwnd_vs_time_mode2_error20.png)
![alt text](./plots/cwnd_vs_time_mode3_error20.png)
![alt text](./plots/cwnd_vs_time_mode4_error20.png)
![alt text](./plots/cwnd_vs_time_mode5_error20.png)

In mode 1,2 and 4 we see that the congestion window gradually increases over time before plateauing. This <br>
is the behavior we expect as eventually sending more packets within a larger window stops being beneficial. <br>
In modes 3 and 5 we see erratic behavior indicating the resetting of the window due to timeout and transmission <br>
failures.

