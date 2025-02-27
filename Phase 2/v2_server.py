#!/usr/bin/env python3
"""
Phase2Server.py - RDT 2.2 Server for EECE 4830-5830 Network Design Project Phase 2
Benjamin Dearden
"""

import os
import socket
import random
import time
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from v2_udp_helpers import checksum, flip_bit

# Configuration constants
SERVER_PORT = 12000
BUFFER_SIZE = 2048
OUTPUT_FOLDER = "cat"

def receive_packet(data, client_address, server_socket, simulation_mode, error_rate):
    """
    Processes an incoming packet and sends the appropriate ACK.
    In simulation mode 3, this function intentionally corrupts the data packet.
    Returns a tuple: (sequence_number, checksum_value, data, finished)
    where finished is True when an "END" message is received.
    """
    try:
        decoded_message = data.decode(errors='ignore')
    except Exception:
        decoded_message = ""

    if decoded_message == "END":
        server_socket.sendto("ACK".encode(), client_address)
        return None, None, None, True

    try:
        parts = data.split(b'|', 2)
        if len(parts) < 3:
            raise ValueError("Malformed packet")
        sequence_number = int(parts[0])
        checksum_value = int(parts[1])
        data_packet = parts[2]
    except Exception as e:
        print(f"Error parsing packet: {e}")
        return None, None, b"", False

    # Option 3: Simulate data packet bit-error at receiver.
    if simulation_mode == 3 and random.random() < error_rate:
        print(f"Simulating data bit-error for packet {sequence_number}")
        data_packet = flip_bit(data_packet)

    if checksum(data_packet) == checksum_value:
        # For Option 2, ACK corruption is now handled at the sender.
        server_socket.sendto(str(sequence_number).encode(), client_address)
        return sequence_number, checksum_value, data_packet, False
    else:
        print(f"Checksum mismatch for packet {sequence_number}")
        # Do not send a valid ACK if checksum fails.
        return sequence_number, checksum_value, b"", False


def flip_bit(data):
    """
    Flips one random bit in the data (used to simulate a bit-error).
    """
    if not data:
        return data
    # Convert bytes to a mutable bytearray
    mutable = bytearray(data)
    total_bits = len(mutable) * 8
    bit_to_flip = random.randrange(total_bits)
    byte_index = bit_to_flip // 8
    bit_index = bit_to_flip % 8
    mutable[byte_index] ^= (1 << bit_index)
    return bytes(mutable)


def run_server(simulation_mode, error_rate):
    """
    Runs the UDP server to receive a file using the RDT 2.2 protocol.
    Returns the total completion time.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("", SERVER_PORT))
    print(
        f"Server listening on port {SERVER_PORT} with simulation mode {simulation_mode} and error rate {error_rate * 100:.0f}%")

    file_data = bytearray()
    last_sequence = -1
    finished = False
    start_time = time.time()

    while not finished:
        try:
            message, client_address = server_socket.recvfrom(BUFFER_SIZE)
            sequence_number, chk, data, finished = receive_packet(
                message, client_address, server_socket, simulation_mode, error_rate
            )
            if sequence_number is not None and sequence_number != last_sequence:
                file_data.extend(data)
                last_sequence = sequence_number
        except Exception as e:
            print(f"Server error: {e}")
    # Ensure the output folder exists
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    # Create a unique output file name based on simulation mode and error rate.
    error_percent = int(error_rate * 100)
    output_file = os.path.join(OUTPUT_FOLDER, f"transmitted_cat_mode{simulation_mode}_error{error_percent}.jpg")
    with open(output_file, "wb") as f:
        f.write(file_data)
    server_socket.close()
    completion_time = time.time() - start_time
    print(f"File saved as {output_file} in {completion_time:.2f} seconds.")
    return completion_time
    # with open(OUTPUT_FILE, "wb") as f:
    #     f.write(file_data)
    # server_socket.close()
    # completion_time = time.time() - start_time
    # print(f"File saved as {OUTPUT_FILE} in {completion_time:.2f} seconds.")
    # return completion_time


def plot_performance(loss_percentages, completion_times, simulation_mode):
    """
    Plots the file transmission completion time against error rates.
    """
    plt.figure(figsize=(10, 5))
    plt.plot(loss_percentages, completion_times, marker='o')
    plt.title(f'Completion Time vs Error Rate (Simulation Mode {simulation_mode})')
    plt.xlabel('Error Rate (%)')
    plt.ylabel('Completion Time (s)')
    plt.grid(True)
    plt.show()


def main():
    # For standalone running, default to Option 1 (no errors) and a single test.
    simulation_mode = 1  # 1: No errors; 2: ACK errors; 3: Data errors.
    error_rate = 0.0
    run_server(simulation_mode, error_rate)


if __name__ == "__main__":
    main()
