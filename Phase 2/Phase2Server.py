"""
Benjamin Dearden
EECE 4830
Project Phase 1 Server
"""
from socket import *


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


def main():
    serverPort = 12000
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(("", serverPort))
    print(f"The server is ready to receive on port {serverPort}")
    file_data = b""
    file_name = "transmitted_cat.jpg"

    while True:
        try:
            message, clientAddress = serverSocket.recvfrom(2048)

            packet = message
            file_data = receive_packet(packet, clientAddress, file_data, file_name, serverSocket)
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
