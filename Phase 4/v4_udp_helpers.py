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
import logging

if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("simulation.log", mode="a"),
            logging.StreamHandler()
        ]
    )

# Disable noisy loggers from PIL and matplotlib
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)

logger = logging.getLogger("UDPHelpers")

random.seed(123)

def debug_print(msg):
    logger.debug(msg)

def checksum(data):
    if len(data) % 2 == 1:
        data += b'\x00'
    total = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i + 1]
        total += word
        total = (total & 0xFFFF) + (total >> 16)
    return ~total & 0xFFFF

def flip_bit(data):
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
