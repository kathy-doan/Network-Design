# ReadMe File

---

### Title and Authors
* Phase 2
* Benjamin Dearden
* Michael Smith
* Peter Dingue
* Kathy Doan

### Environment
* Windows 10/11
* Python
* Python 3.12
* PyCharm IDE 2024.1.1

### Purpose of The Phase
This phase's purpose is to implement rdt 2.2 on top of phase 1 rdt 1.0. The protocol provides reliable data transfer over an unreliable network with simulated errors. <br>

### Instructions
1. install matplotlib (if you dont have this library yet)
2. run the test harness -- python simulate_rdt.py (this will test all error rates from 0% to 60% and generate the performance plots)
3. run the server -- python UDP_server.py
4. run the client -- python UDP_client.py
5. 4. run the GUI for a more interactive setup -- python tkinter_gui.py
6. Edit TRIALS to desired amount
