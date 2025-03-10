#!/usr/bin/env python3
"""
Benjamin Dearden
Michael Smith
Peter Dingue
Kathy Doan

v3_udp_helpers.py - Helper functions for RDT 3.0 implementation
Simulation Modes:
    1: No errors.
    2: ACK packet bit-error.
    3: Data packet bit-error.
    4: ACK packet loss.
    5: (Handled at server) Data packet loss.
"""
import random
import select
import time

DEBUG = False


def debug_print(msg):
    if DEBUG:
        print(msg)


def checksum(data):
    """
    Computes a 16-bit one's complement sum over 16-bit words.
    """
    if len(data) % 2 == 1:
        data += b'\x00'
    total = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1]
        total += word
        total = (total & 0xFFFF) + (total >> 16)
    return ~total & 0xFFFF


def flip_bit(data):
    """
    Flips one random bit in the data to simulate corruption.
    """
    if not data:
        return data
    mutable = bytearray(data)
    total_bits = len(mutable) * 8
    bit_to_flip = random.randrange(total_bits)
    byte_index = bit_to_flip // 8
    bit_index = bit_to_flip % 8
    mutable[byte_index] ^= (1 << bit_index)
    return bytes(mutable)


def make_packet(file_name, sequence_number, packet_size=1024):
    """
    Reads a chunk of data from the file and constructs a packet with a header:
        "<sequence_number>|<checksum>|<data>"
    Returns None if there is no more data.
    """
    try:
        with open(file_name, "rb") as file_to_send:
            file_to_send.seek(sequence_number * packet_size)
            data = file_to_send.read(packet_size)
    except FileNotFoundError:
        debug_print(f"File not found: {file_name}")
        return None

    if not data:
        return None

    chk_value = checksum(data)
    header = f"{sequence_number}|{chk_value}|".encode()
    return header + data


def send_packet(packet, server_address, server_port, client_socket, sequence_number,
                simulation_mode, error_rate, timeout):
    """
    Sends a packet over UDP and waits for the correct ACK using an explicit countdown timer.
    In simulation mode 2, simulates ACK bit-error.
    In simulation mode 4, simulates ACK loss.
    The sender retransmits if the timeout expires or an incorrect ACK is received.
    Returns the number of retransmissions for this packet.
    """
    retransmission_count = 0
    while True:
        client_socket.sendto(packet, (server_address, server_port))
        debug_print(f"Packet sent: {sequence_number}")
        start_time = time.time()
        ready = select.select([client_socket], [], [], timeout)
        if ready[0]:
            acknowledgement, _ = client_socket.recvfrom(2048)
            try:
                ack_sequence_number = int(acknowledgement.decode())
            except Exception:
                ack_sequence_number = -1

            # Simulation mode 2: simulate ACK bit-error by flipping a bit.
            if simulation_mode == 2 and random.random() < error_rate:
                debug_print(f"Simulating ACK bit-error for packet {sequence_number}")
                ack_sequence_number ^= 0x01

            # Simulation mode 4: simulate ACK loss by ignoring the received ACK.
            if simulation_mode == 4 and random.random() < error_rate:
                debug_print(f"Simulating ACK loss for packet {sequence_number}")
                retransmission_count += 1
                continue

            if ack_sequence_number == sequence_number:
                debug_print(f"Packet acknowledged: {ack_sequence_number}")
                break
            else:
                debug_print(f"ACK mismatch: received {ack_sequence_number}, expected {sequence_number}. Retrying...")
                retransmission_count += 1
                continue
        else:
            # Timeout expired
            retransmission_count += 1
            debug_print(f"Timeout for packet {sequence_number}. Retransmitting...")
    return retransmission_count
