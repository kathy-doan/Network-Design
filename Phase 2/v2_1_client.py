#!/usr/bin/env python3
"""
v2_client.py - RDT 2.2 Client
This client sends a file using the RDT 2.2 protocol.
It accepts a simulation_mode:
    Mode 1 (None): No errors.
    Mode 2 (Ack): Simulated ACK bit-errors.
    Mode 3 (Data): Simulated Data bit-errors.
"""

import socket
import time
from v2_1_udp_helpers import make_packet, send_packet

DEBUG = True

def debug_print(msg):
    if DEBUG:
        print(msg)

SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 12000
FILE_TO_SEND = "cat.bmp"  # Replace with a larger file if needed
PACKET_SIZE = 1024
TIMEOUT = 0.01

def send_file(simulation_mode, error_rate):
    """
    Reads the file and sends it in packets using the RDT 2.2 protocol.
    In mode 2, the sender will simulate ACK bit-errors.
    """
    sequence_number = 0
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(TIMEOUT)
    try:
        while True:
            packet = make_packet(FILE_TO_SEND, sequence_number, PACKET_SIZE)
            if packet is None:
                client_socket.sendto("END".encode(), (SERVER_ADDRESS, SERVER_PORT))
                break

            send_packet(packet, SERVER_ADDRESS, SERVER_PORT, client_socket,
                        sequence_number, simulation_mode, error_rate)
            sequence_number += 1
    except Exception as e:
        debug_print(f"Client encountered error: {e}")
    finally:
        client_socket.close()

def main():
    simulation_mode = 1  # Default to mode 1 (None)
    error_rate = 0.0
    start = time.time()
    send_file(simulation_mode, error_rate)
    end = time.time()
    debug_print(f"File sent in {end - start:.2f} seconds.")

if __name__ == "__main__":
    main()
