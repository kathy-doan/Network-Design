#!/usr/bin/env python3
"""
Benjamin Dearden
Michael Smith
Peter Dingue
Kathy Doan

v4_client.py - Go-Back-N Client for EECE 4830-5830 Network Design Project Phase 4
Simulation Modes:
    1: No errors.
    2: Simulated ACK packet bit-errors.
    3: Simulated DATA packet bit-errors.
    4: Simulated ACK packet loss.
    5: Simulated DATA packet loss.

This implementation uses a sliding window (of fixed size WINDOW_SIZE) to allow multiple
packets to be in-flight. A single timer is maintained for the oldest unacknowledged packet;
if the timer expires, all packets in the window are retransmitted.
"""
import socket
import time
import os
import select
import random
from v4_udp_helpers import make_packet, debug_print

DEBUG = True


def debug_print(msg):
    if DEBUG:
        print(msg)


SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 12000
FILE_TO_SEND = "cat.bmp"  # Replace with a larger file if needed
PACKET_SIZE = 1024
TIMEOUT = 0.03  # Timeout value in seconds (30-50ms recommended)
WINDOW_SIZE = 10  # Fixed window size for Go-Back-N


def send_file(simulation_mode, error_rate):
    """
    Reads the file and sends it in packets using the Go-Back-N protocol.
    Implements a sliding window mechanism, a single timer for the base packet,
    and cumulative ACK handling.

    Simulation Modes:
      2: Simulate ACK packet bit-errors.
      4: Simulate ACK packet loss.

    Returns a tuple: (client_completion_time, total_retransmissions, throughput in bytes/s).
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setblocking(False)  # Enable non-blocking mode

    base = 0
    next_seq = 0
    packets = {}  # Buffer: sequence number -> packet
    total_retransmissions = 0
    timer = None  # Timer for the oldest unacknowledged packet
    file_end = False  # Indicates whether the entire file has been read

    start_time = time.time()

    while True:
        # Send new packets if window is not full and file is not finished
        while next_seq < base + WINDOW_SIZE and not file_end:
            packet = make_packet(FILE_TO_SEND, next_seq, PACKET_SIZE)
            if packet is None:
                file_end = True
                break
            client_socket.sendto(packet, (SERVER_ADDRESS, SERVER_PORT))
            debug_print(f"Packet {next_seq} sent")
            packets[next_seq] = packet
            if base == next_seq:
                timer = time.time()  # Start timer for base packet
            next_seq += 1

        # Check for incoming ACKs
        try:
            ready = select.select([client_socket], [], [], 0.01)[0]
        except Exception:
            ready = []
        if ready:
            try:
                ack_data, _ = client_socket.recvfrom(2048)
                try:
                    ack_num = int(ack_data.decode())
                except:
                    ack_num = -1

                # Simulation mode 2: simulate ACK bit-error by flipping a bit
                if simulation_mode == 2 and random.random() < error_rate:
                    debug_print(f"Simulating ACK bit-error for received ACK {ack_num}")
                    ack_num ^= 0x01

                # Simulation mode 4: simulate ACK loss by ignoring the ACK
                if simulation_mode == 4 and random.random() < error_rate:
                    debug_print(f"Simulating ACK loss for received ACK {ack_num}")
                    ack_num = -1

                if ack_num >= base:
                    debug_print(f"ACK {ack_num} received, sliding window")
                    base = ack_num + 1
                    if base == next_seq:
                        timer = None  # Stop timer if no outstanding packets
                    else:
                        timer = time.time()  # Restart timer for new base
            except Exception as e:
                debug_print(f"Error receiving ACK: {e}")

        # Check for timeout on the base packet
        if timer is not None and (time.time() - timer) > TIMEOUT:
            debug_print(f"Timeout occurred. Retransmitting packets from {base} to {next_seq - 1}")
            for seq in range(base, next_seq):
                client_socket.sendto(packets[seq], (SERVER_ADDRESS, SERVER_PORT))
                total_retransmissions += 1
            timer = time.time()  # Restart timer after retransmission

        # Exit condition: file is finished and all packets have been acknowledged
        if file_end and base == next_seq:
            client_socket.sendto("END".encode(), (SERVER_ADDRESS, SERVER_PORT))
            break

    end_time = time.time()
    client_socket.close()
    completion_time = end_time - start_time
    file_size = os.path.getsize(FILE_TO_SEND)
    throughput = file_size / completion_time  # bytes per second
    debug_print(
        f"File sent in {completion_time:.2f} seconds with {total_retransmissions} retransmissions. Throughput: {throughput:.2f} bytes/s.")
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
