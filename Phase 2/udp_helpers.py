"""
Benjamin Dearden
EECE 4830
Project Phase 1
Helper function
"""
from socket import *


def make_packet_old(file_name, server_name, server_port, client_socket):
    try:
        with open(file_name, "rb") as file_to_read:
            packet_size = 1024
            sequence_number = 0
            while True:
                packet = file_to_read.read(packet_size)
                if not packet:
                    break

                sequenced_packet = bytes(f"{sequence_number}|", 'utf-8') + packet

                client_socket.sendto(sequenced_packet, (server_name, server_port))
                sequence_number += 1

            client_socket.sendto("END".encode(), (server_name, server_port))
            while True:
                data, address = client_socket.recvfrom(1024)
                if data.decode() == "ACK":
                    break
    except Exception as e:
        print(f"Error while sending packets: {e}")


def checksum(data):
    return sum(data) % 256


def send_packet(packet, server_name, server_port, client_socket, sequence_number):
    while True:
        client_socket.sendto(packet, (server_name, server_port))
        print(f"Packet sent: {sequence_number}")
        try:
            acknowledgement, _ = client_socket.recvfrom(2048)
            ack_sequence_number = int(acknowledgement.decode())
            if ack_sequence_number == sequence_number:
                break
            else:
                print(f"Sequence number mismatch: {ack_sequence_number}, expected {sequence_number}")
        except timeout:
            print(f"ACK not received for {sequence_number}, resending packet.")


def make_packet(file_name, sequence_number):
    with open(file_name, "rb") as file_to_send:
        file_to_send.seek(sequence_number * 1024)
        data = file_to_send.read(1024)

    if not data:
        return None
    checksum_value = checksum(data)
    return bytes(f"{sequence_number}| {checksum_value}|", 'utf-8') + data
