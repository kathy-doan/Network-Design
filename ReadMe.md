# ReadMe File

---

### Title and Authors
* Phase 2
* Benjamin Dearden
* Michael
* Peter
* Kathy

### Environment
* Windows 10/11
* Python
* Python 3.12
* PyCharm IDE 2024.1.1

### Purpose of The Phase
This phase's purpose is to implement rdt 2.2 on top of phase 1 rdt 1.0. The protocol provides reliable data transfer over an unreliable network with simulated errors. <br>

### Instructions
1. install matplotlib (if you dont have this library yet)
2. run the test harness -- python haypness.py (this will test all error rates from 0% to 60% and generate the performance plots)
3. run the server -- python v2_server.py
4. run the client -- python v2_client.py
5. edit SIMULATION_MODE from harness.py to selects between different error scenarios (option 1 = no errors and option 2 = ack errors and option 3 = data packet errors)
7. change ERROR_RATES to select test conditions
