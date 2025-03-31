#!/usr/bin/env python3
"""
Benjamin Dearden
Michael Smith
Peter Dingue
Kathy Doan

v4_udp_helpers.py - Helper functions for Go-Back-N implementation
Simulation Modes:
    1: No errors.
    2: ACK packet bit-error.
    3: Data packet bit-error.
    4: ACK packet loss.
    5: (Handled at server) Data packet loss.

Note: The previous send_packet function (used for stop-and-wait) is no longer used,
as the client now manages transmission and ACK handling directly.
"""
import random
import select
import time

DEBUG = True
random.seed(123)


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
        word = (data[i] << 8) + data[i + 1]
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

# Note: The send_packet function from earlier phases is not used in the Go-Back-N implementation.
