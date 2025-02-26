"""
Benjamin Dearden
EECE 4830
Project Phase 1 Server
"""
from socket import *
from udp_helpers import checksum
import random


def receive_packet(data, client_address, server_socket):
    decoded_message = data.decode(errors='ignore')
    if decoded_message == "END":
        print(f"Received END message from {client_address}, closing connection")
        server_socket.sendto("ACK".encode(), client_address)
        return None, True
    else:
        sequence_number, checksum_value, data_packet = data.split(b'|', 2)
        sequence_number = int(sequence_number)
        checksum_value = int(checksum_value)

        if checksum(data_packet) == checksum_value:
            if random.random() < 0.1:
                print(f"Simulating bit error in ACK for packet {sequence_number}")
                return None, False
                #  server_socket.sendto(str(sequence_number + 1).encode(), client_address)
            else:
                server_socket.sendto(str(sequence_number).encode(), client_address)
            print(f"Received packet {sequence_number} from {client_address} with current checksum"
                  f", sending ACK, packet size: {len(data_packet)} bytes")
            return data_packet, False
        else:
            print(f"Received incorrect packet from {client_address}, ignoring")
            return b"", False


'''
def receive_packet(data, client_address, file_data, file_name, server_socket):
    decoded_message = data.decode(errors="ignore")
    if decoded_message == "END":
        print(f"Received END message from {client_address}, saving data to {file_name}")
        with open(file_name, "wb") as file:
            file.write(file_data)
        print(f"File {file_name} saved successfully")
        server_socket.sendto("ACK".encode(), client_address)
        return b""  # Reset file_data after saving
    else:
        sequence_number, data_packet = data.split(b'|', 1)
        print(f"Received data packet from {client_address} with sequence number"
              f" {int(sequence_number)} and size: {len(data_packet)} bytes")

    return file_data + data_packet
'''


def main():
    server_port = 12000
    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind(("", server_port))
    print(f"The server is ready to receive on port {server_port}")
    file_name = "transmitted_cat.jpg"
    file_data = bytearray()
    #  file_data = b""
    #  file_name = "transmitted_cat.jpg"

    while True:
        try:
            message, client_address = server_socket.recvfrom(2048)
            data, finished = receive_packet(message, client_address, server_socket)
            if data is not None:
                file_data.extend(data)
            if finished:
                with open(file_name, "wb") as file:
                    file.write(file_data)
                print(f"File {file_name} saved successfully")
                file_data = bytearray()  # clear
        except Exception as e:
            print(f"Error: {e}")


'''
    while True:
        try:
            message, clientAddress = serverSocket.recvfrom(2048)

            packet = message
            file_data = receive_packet(packet, clientAddress, file_data, file_name, serverSocket)
        except Exception as e:
            print(f"Error: {e}")
'''


if __name__ == "__main__":
    main()
