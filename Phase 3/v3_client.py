#!/usr/bin/env python3
"""
Benjamin Dearden
Michael Smith
Peter Dingue
Kathy Doan

v3_client.py - RDT 3.0 Client for EECE 4830-5830 Network Design Project Phase 3
Simulation Modes:
    1: No errors.
    2: Simulated ACK packet bit-errors.
    3: Simulated DATA packet bit-errors.
    4: Simulated ACK packet loss.
    5: Simulated DATA packet loss.
"""
import socket
import time
import os
from v3_udp_helpers import make_packet, send_packet, debug_print

DEBUG = False

def debug_print(msg):
    if DEBUG:
        print(msg)

SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 12000
FILE_TO_SEND = "cat.bmp"  # Replace with a larger file if needed
PACKET_SIZE = 1024
# Timeout value in seconds (30-50ms recommended)
TIMEOUT = 0.03


def send_file(simulation_mode, error_rate):
    """
    Reads the file and sends it in packets using the RDT 3.0 protocol.
    Returns a tuple: (client_completion_time, total_retransmissions, throughput in bytes/s).
    In simulation mode 2, the sender will simulate ACK bit-errors.
    In simulation mode 4, the sender simulates ACK loss.
    """
    sequence_number = 0
    total_retransmissions = 0
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # (Explicit timer for retransmission)
    start = time.time()
    while True:
        packet = make_packet(FILE_TO_SEND, sequence_number, PACKET_SIZE)
        if packet is None:
            client_socket.sendto("END".encode(), (SERVER_ADDRESS, SERVER_PORT))
            break

        retrans = send_packet(packet, SERVER_ADDRESS, SERVER_PORT, client_socket,
                                sequence_number, simulation_mode, error_rate, TIMEOUT)
        total_retransmissions += retrans
        sequence_number += 1
    end = time.time()
    client_socket.close()
    completion_time = end - start
    file_size = os.path.getsize(FILE_TO_SEND)
    throughput = file_size / completion_time  # bytes per second
    debug_print(f"File sent in {completion_time:.2f} seconds with {total_retransmissions} retransmissions. Throughput: {throughput:.2f} bytes/s.")
    return completion_time, total_retransmissions, throughput

def main():
    simulation_mode = 1  # Change mode as needed: 1-5
    error_rate = 0.0
    start = time.time()
    send_file(simulation_mode, error_rate)
    end = time.time()
    debug_print(f"File sent in {end - start:.2f} seconds.")

if __name__ == "__main__":
    main()
