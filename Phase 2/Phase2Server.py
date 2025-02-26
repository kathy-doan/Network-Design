"""
Benjamin Dearden
EECE 4830
Project Phase 1 Server
"""
from socket import *
from udp_helpers import checksum
import random
import time
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


def receive_packet(data, client_address, server_socket, error_rate):
    decoded_message = data.decode(errors='ignore')
    sequence_number = None
    checksum_value = None
    data_packet = None
    if decoded_message == "END":
        print(f"Received END message from {client_address}, closing connection")
        server_socket.sendto("ACK".encode(), client_address)
        return sequence_number, checksum_value, data_packet, True
    else:
        sequence_number, checksum_value, data_packet = data.split(b'|', 2)
        sequence_number = int(sequence_number)
        checksum_value = int(checksum_value)
        if random.random() < error_rate:
            print(f"Simulating bit error for packet {sequence_number}")
            data_packet = flip_bit(data_packet)
        if checksum(data_packet) == checksum_value:
            if random.random() < error_rate:
                print(f"Simulating bit error in ACK for packet {sequence_number}")
                server_socket.sendto(str(sequence_number + 1).encode(), client_address)
            else:
                server_socket.sendto(str(sequence_number).encode(), client_address)
            print(f"Received packet {sequence_number} from {client_address} with current checksum"
                  f", sending ACK, packet size: {len(data_packet)} bytes")
            return sequence_number, checksum_value, data_packet, False
        else:
            print(f"Received incorrect packet from {client_address}, ignoring")
            return sequence_number, checksum_value, b"", False


def flip_bit(data):
    bit_error_index = random.randrange(len(data) * 8)
    byte_index = bit_error_index // 8
    bit_index = bit_error_index % 8
    data[byte_index] = data[byte_index] ^ (1 << bit_index)
    return data

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


def main(error_rate):
    server_port = 12000
    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind(("", server_port))
    print(f"The server is ready to receive on port {server_port}")
    file_name = "transmitted_cat.jpg"
    file_data = bytearray()
    last_success = -1
    #  file_data = b""
    #  file_name = "transmitted_cat.jpg"
    while True:
        try:
            message, client_address = server_socket.recvfrom(2048)
            sequence_number, checksum_value, data, finished = (
                receive_packet(message, client_address, server_socket, error_rate))

            if data is not None and sequence_number != last_success:
                file_data.extend(data)
                last_success = sequence_number
            if finished:
                with open(file_name, "wb") as file:
                    file.write(file_data)
                print(f"File {file_name} saved successfully")
                file_data = bytearray()  # clear
                return
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
    loss_percentages = list(range(0, 65, 5))
    completion_times = []

    for loss_percentage in loss_percentages:
        start_time = time.time()
        # main(loss_percentage / 100.0)
        main(0.0) # EDIT ME TO CREATE LOOP
        end_time = time.time()

        completion_time = end_time - start_time
        completion_times.append(completion_time)

    plt.figure(figsize=(10, 5))
    plt.plot(loss_percentages, completion_times, marker='o')
    plt.title('File Transmission Completion Time vs Error Rate')
    plt.xlabel('Loss/Error Rate (%)')
    plt.ylabel('Completion Time (s)')
    plt.grid(True)
    plt.show()

    # main()

