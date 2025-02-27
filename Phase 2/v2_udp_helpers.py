#!/usr/bin/env python3
"""
udp_helpers.py - Helper functions for RDT 2.2 implementation
Benjamin Dearden
"""

import random

DEBUG = False  # Set to True to enable debug output

def debug_print(msg):
    if DEBUG:
        print(msg)

def checksum(data):
    """
    Computes a checksum using a one's complement sum over 16-bit words.
    This function:
      1. Pads the data with a zero byte if its length is odd.
      2. Processes the data in 16-bit chunks.
      3. Sums the chunks with wrap-around.
      4. Returns the one's complement of the sum.
    """
    if len(data) % 2 == 1:
        data += b'\x00'
    total = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1]
        total += word
        total = (total & 0xFFFF) + (total >> 16)
    checksum_value = ~total & 0xFFFF
    return checksum_value

def flip_bit(data):
    """
    Flips one random bit in the data.
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
    Reads a chunk of data from the file and constructs a packet with a header
    containing the sequence number and checksum.
    The header format is: "<sequence_number>|<checksum>|"
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

def send_packet(packet, server_address, server_port, client_socket, sequence_number, simulation_mode, error_rate):
    """
    Sends a packet over UDP and waits for the correct ACK.
    In simulation mode 2, the function intentionally corrupts the received ACK
    (with probability error_rate). Retransmits the packet until the correct ACK is received.
    """
    while True:
        client_socket.sendto(packet, (server_address, server_port))
        debug_print(f"Packet sent: {sequence_number}")
        try:
            acknowledgement, _ = client_socket.recvfrom(2048)
            try:
                ack_sequence_number = int(acknowledgement.decode())
            except Exception:
                ack_sequence_number = -1

            if simulation_mode == 2 and random.random() < error_rate:
                debug_print(f"Simulating ACK bit-error for packet {sequence_number}")
                ack_sequence_number ^= 0x01  # Flip the least significant bit

            if ack_sequence_number == sequence_number:
                debug_print(f"Packet acknowledged: {ack_sequence_number}")
                break
            else:
                debug_print(f"ACK mismatch: received {ack_sequence_number}, expected {sequence_number}. Retrying...")
        except Exception as e:
            debug_print(f"ACK not received for packet {sequence_number} (Error: {e}). Resending...")
