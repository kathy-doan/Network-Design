# Design File

---

### Title and Authors
* Phase 1
* Benjamin Dearden

### Purpose of The Phase
This phase's purpose is to become familiar with
socket programming.
### Code Explanation

[![block 1](/rec_pack.png)]

The above block of code handles the receiving of packets from the client. <br>
If there are no more packets it will save the packets received.

[![block 2](/make_pack.png)]

This block of code is responsible for creating packets to send to the client. <br>
It will check if there are any packets to send and then send them.

[![block 3](/hello_msg.png)]

This block of code was used to verify message sending functionality <br>
within the client and server. Once the client and server were verified to <br>
be communicating these lines were commented out and packet sending <br>
functionality was implemented.

[![block 4](/client_console.png)]

The client console will look like this once the client is run while <br>
the server is running.

[![block 5](/server_console.png)]

This is how the server console will look when the server is running. <br>
Once the packets have completing sending the final message will display <br>
noting that the transmitted_image.bmp was successfully saved.