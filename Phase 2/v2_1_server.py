#!/usr/bin/env python3
"""
v2_server.py - RDT 2.2 Server
This server receives a file over UDP using the RDT 2.2 protocol.
It supports:
    Mode 1 (None): No errors.
    Mode 2 (Ack): No simulation on the server.
    Mode 3 (Data): Simulated Data bit-errors on the payload.
"""

import os
import socket
import random
import time
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from v2_1_udp_helpers import checksum, flip_bit

DEBUG = True
# DATA_THRESHOLD and retransmission tracking removed

def debug_print(msg):
    if DEBUG:
        print(msg)

SERVER_PORT = 12000
BUFFER_SIZE = 2048
OUTPUT_FOLDER = "cat"

def receive_packet(data, client_address, server_socket, simulation_mode, error_rate,
                   expected_seq, last_valid_ack):
    """
    Processes an incoming packet and sends the appropriate ACK.
    In mode 3, simulates a data bit-error on the payload with probability = error_rate.
    Returns: (received_sequence_number, is_in_order, payload, finished)
    """
    try:
        decoded_message = data.decode(errors='ignore')
        if decoded_message == "END":
            server_socket.sendto("ACK".encode(), client_address)
            return None, False, None, True
    except:
        pass

    try:
        parts = data.split(b'|', 2)
        if len(parts) < 3:
            raise ValueError("Malformed packet")
        sequence_number = int(parts[0])
        checksum_value = int(parts[1])
        payload = parts[2]
    except Exception as e:
        debug_print(f"Error parsing packet: {e}")
        server_socket.sendto(str(last_valid_ack).encode(), client_address)
        return None, False, b"", False

    if simulation_mode == 3 and random.random() < error_rate:
        debug_print(f"Simulating data bit-error for packet {sequence_number}")
        payload = flip_bit(payload)

    if checksum(payload) == checksum_value:
        if sequence_number == expected_seq:
            server_socket.sendto(str(sequence_number).encode(), client_address)
            return sequence_number, True, payload, False
        else:
            server_socket.sendto(str(last_valid_ack).encode(), client_address)
            return sequence_number, False, b"", False
    else:
        debug_print(f"Checksum mismatch for packet {sequence_number}")
        server_socket.sendto(str(last_valid_ack).encode(), client_address)
        return sequence_number, False, b"", False

def run_server(simulation_mode, error_rate):
    """
    Runs the UDP server to receive a file using the RDT 2.2 protocol.
    Returns the total completion time.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("", SERVER_PORT))
    debug_print(f"Server listening on port {SERVER_PORT} with simulation mode {simulation_mode} and error rate {error_rate * 100:.0f}%")

    file_data = bytearray()
    expected_seq = 0
    last_valid_ack = -1
    finished = False
    start_time = time.time()

    while not finished:
        try:
            message, client_address = server_socket.recvfrom(BUFFER_SIZE)
            debug_print(f"Received packet for expected_seq {expected_seq}")
            seq_num, in_order, payload, finished = receive_packet(
                message,
                client_address,
                server_socket,
                simulation_mode,
                error_rate,
                expected_seq,
                last_valid_ack
            )
            if finished:
                break
            if seq_num is not None and in_order:
                debug_print(f"Packet {seq_num} accepted. Moving to next sequence.")
                file_data.extend(payload)
                last_valid_ack = seq_num
                expected_seq += 1
            # No retransmission count tracking here.
        except Exception as e:
            debug_print(f"Server error: {e}")

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    error_percent = int(error_rate * 100)
    output_file = os.path.join(OUTPUT_FOLDER, f"transmitted_cat_mode{simulation_mode}_error{error_percent}.bmp")
    with open(output_file, "wb") as f:
        f.write(file_data)

    server_socket.close()
    completion_time = time.time() - start_time
    debug_print(f"File saved as {output_file} in {completion_time:.2f} seconds.")
    return completion_time

def plot_performance(all_error_percentages, all_completion_times, modes, trials):
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 5))
    # Use custom labels: Mode 1 -> "None", Mode 2 -> "Ack", Mode 3 -> "Data"
    mode_labels = {1: "None", 2: "Ack", 3: "Data"}
    for mode in modes:
        plt.plot(all_error_percentages, all_completion_times[mode], marker='o', label=mode_labels.get(mode, str(mode)))
    plt.title(f'Completion Time vs Error Rate for Different Modes (Trials: {trials})')
    plt.xlabel('Error Rate (%)')
    plt.ylabel('Completion Time (s)')
    plt.grid(True)
    plt.legend()
    plt.show()

def main():
    simulation_mode = 1
    error_rate = 0.0
    run_server(simulation_mode, error_rate)

if __name__ == "__main__":
    main()
