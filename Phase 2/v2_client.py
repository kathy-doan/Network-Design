#!/usr/bin/env python3
"""
Phase2Client.py - RDT 2.2 Client for EECE 4830-5830 Network Design Project Phase 2
Benjamin Dearden
Michael Smith
Peter Dingue
Kathy Doan
"""

import socket
import time
from v2_udp_helpers import make_packet, send_packet

DEBUG = False  # Set to True to enable debug output

def debug_print(msg):
    if DEBUG:
        print(msg)

# Configuration constants
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 12000
FILE_TO_SEND = "cat.jpg"
PACKET_SIZE = 1024
TIMEOUT = 0.01

def send_file(simulation_mode, error_rate):
    """
    Reads the file and sends it in packets using the RDT 2.2 protocol.
    In simulation mode 2, the sender will simulate ACK bit-errors.
    """
    sequence_number = 0
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(TIMEOUT)
    try:
        while True:
            packet = make_packet(FILE_TO_SEND, sequence_number, PACKET_SIZE)
            if packet is None:
                # No more data; signal end of transmission
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
    # For standalone running, default to Option 1 (no errors) and error_rate 0.
    simulation_mode = 1  # 1: No errors; 2: ACK errors; 3: Data errors.
    error_rate = 0.0
    start = time.time()
    send_file(simulation_mode, error_rate)
    end = time.time()
    debug_print(f"File sent in {end - start:.2f} seconds.")

if __name__ == "__main__":
    main()
