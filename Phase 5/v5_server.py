
# Modified v5_server.py for Simplified TCP with Proper Teardown
import socket
import os
import time
import random
import logging
from v5_helpers import checksum, flip_bit

random.seed(123)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [SERVER] %(message)s', handlers=[logging.FileHandler("tcp_simulation.log")])
logger = logging.getLogger("Server")

SERVER_PORT = 12000
BUFFER_SIZE = 2048
OUTPUT_FOLDER = "cat"

# TCP flags
SYN = "SYN"
SYN_ACK = "SYN-ACK"
ACK = "ACK"
FIN = "FIN"

def tcp_handshake(sock):
    logger.debug("Waiting for client handshake")
    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        msg = data.decode(errors='ignore')
        if msg == SYN:
            sock.sendto(SYN_ACK.encode(), addr)
        elif msg == ACK:
            logger.debug("Handshake complete")
            return addr

def tcp_teardown(sock, addr):
    try:
        sock.sendto(ACK.encode(), addr)
        logger.debug("Connection teardown acknowledged")
    except Exception as e:
        logger.debug(f"Teardown error: {e}")

def run_server(simulation_mode, error_rate):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", SERVER_PORT))
    addr = tcp_handshake(sock)

    expected_seq = 0
    file_data = bytearray()
    last_valid_ack = -1
    start_time = time.time()

    while True:
        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            msg = data.decode(errors='ignore')

            if msg in [SYN, ACK]:
                continue
            elif msg == FIN:
                tcp_teardown(sock, addr)
                break

            parts = data.split(b"|", 2)
            if len(parts) < 3:
                sock.sendto(str(last_valid_ack).encode(), addr)
                continue
            seq = int(parts[0])
            chksum = int(parts[1])
            payload = parts[2]

            if simulation_mode == 5 and random.random() < error_rate:
                logger.debug(f"Simulating loss for packet {seq}")
                sock.sendto(str(last_valid_ack).encode(), addr)
                continue

            if simulation_mode == 3 and random.random() < error_rate:
                payload = flip_bit(payload)

            if checksum(payload) == chksum:
                if seq == expected_seq:
                    file_data.extend(payload)
                    last_valid_ack = seq
                    expected_seq += 1
                sock.sendto(str(last_valid_ack).encode(), addr)
            else:
                logger.debug(f"Checksum mismatch for {seq}")
                sock.sendto(str(last_valid_ack).encode(), addr)
        except Exception as e:
            logger.debug(f"Server error: {e}")
            break

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    output_file = os.path.join(OUTPUT_FOLDER, f"tcp_output_mode{simulation_mode}_error{int(error_rate * 100)}.bmp")
    with open(output_file, "wb") as f:
        f.write(file_data)

    sock.close()
    duration = time.time() - start_time
    logger.debug(f"Saved file {output_file} in {duration:.2f} seconds")
    return duration

if __name__ == "__main__":
    run_server(1, 0.0)
