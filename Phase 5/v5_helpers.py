# Updated v5_helpers.py for TCP-like Segment Handling
import random
import logging

ENABLE_CONSOLE_LOG = False
log_handlers = [logging.FileHandler("tcp_simulation.log", mode="a")]
if ENABLE_CONSOLE_LOG:
    log_handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
    handlers=log_handlers
)
logger = logging.getLogger("Helpers")

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
        with open(file_name, "rb") as f:
            f.seek(sequence_number * packet_size)
            data = f.read(packet_size)
    except FileNotFoundError:
        debug_print(f"File not found: {file_name}")
        return None

    if not data:
        return None

    chksum = checksum(data)
    header = f"{sequence_number}|{chksum}|".encode()
    return header + data
