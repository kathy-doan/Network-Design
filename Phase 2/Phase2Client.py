# CTRL + ALT + L = Auto format
"""
Benjamin Dearden
EECE 4830
Project Phase 2 Client
"""
from socket import *
from udp_helpers import make_packet
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
    server_name = '127.0.0.1'
    server_port = 12000
    client_socket = socket(AF_INET, SOCK_DGRAM)
    final_message = "All packets sent."

    try:
        make_packet("image.bmp", server_name, server_port, client_socket)
        #send_message(server_name, server_port, client_socket)
    finally:
        print(final_message)
        client_socket.close()

if __name__ == "__main__":
    main()
