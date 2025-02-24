"""
Benjamin Dearden
EECE 4830
Project Phase 1 Server
"""
from socket import *

def receive_packet(data, client_address, file_data, file_name):
        decoded_message = data.decode(errors="ignore")
        if decoded_message == "END":
            print(f"Received END message from {client_address}, saving data to {file_name}")
            with open(file_name, "wb") as file:
                file.write(file_data)
            print(f"File {file_name} saved successfully")
            return b""  # Reset file_data after saving
        else:
            print(f"Received data packet from {client_address}: {len(data)} bytes")

        return file_data + data

def main():
    serverPort = 12000
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(("", serverPort))
    print(f"The server is ready to receive on port {serverPort}")
    file_data = b""
    file_name = "transmitted_image.bmp"

    while True:
        try:
            message, clientAddress = serverSocket.recvfrom(2048)

            packet = message
            file_data = receive_packet(packet, clientAddress, file_data, file_name)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
