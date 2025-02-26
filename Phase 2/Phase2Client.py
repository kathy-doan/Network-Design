# CTRL + ALT + L = Auto format
"""
Benjamin Dearden
EECE 4830
Project Phase 2 Client
"""
from socket import *
from udp_helpers import *


'''
send_message function is for sending hello from client to server
def send_message(server_name, server_port, client_socket):
    try:
        #message = input('Input lowercase sentence:')
        #print(f"Sending to server {server_name}:{server_port}: {message}")

        #client_socket.sendto(message.encode(), (server_name, server_port))
        modifiedMessage, serverAddress = client_socket.recvfrom(2048)
        print(f"Response from server: {modifiedMessage.decode()}")
    except Exception as e:
        print(f"Error while sending message: {e}")
'''


def main():
    # for i in range(13): EDIT HERE TO CREATE LOOP
    server_name = '127.0.0.1'
    server_port = 12000
    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.settimeout(1.0)  # timeout for receive function
    final_message = "All packets sent."
    sequence_number = 0  # packet sequence number to maintain packet order
    while True:
        try:
            packet = make_packet("cat.jpg", sequence_number)
            if packet is None:  # no more packets
                client_socket.sendto("END".encode(), (server_name, server_port))
                break
            send_packet(packet, server_name, server_port, client_socket, sequence_number)
            sequence_number += 1
        except Exception as e:
            print(f"Error: {e}")
    print("All packets sent.")
    client_socket.close()


'''    
    try:
        make_packet_old("cat.jpg", server_name, server_port, client_socket)
        #send_message(server_name, server_port, client_socket)
    finally:
        print(final_message)
        client_socket.close()
'''
if __name__ == "__main__":
    main()
