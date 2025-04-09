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
packets to be in-flight and supports enabling/disabling of loss recovery.
When loss recovery is enabled, a timer is maintained for the oldest unacknowledged packet;
if the timer expires, all packets in the window are retransmitted.
When loss recovery is disabled, the client sends each packet once and then sends "END" immediately.
ACK errors in modes 2 and 4 are now simulated by returning a random value in the range [base, correct_ack - 1]
(without duplicate ACK detection), ensuring the returned ACK is always less than the correct value.
"""

import socket
import time
import os
import select
import random
import logging
from v4_udp_helpers import make_packet

# Configure logging if not already configured.
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("simulation.log", mode="a"),
            # logging.StreamHandler()  <-- Console output disabled
        ]
    )

# Disable noisy loggers from PIL and matplotlib
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)

# Create a logger for this module (source: Client)
logger = logging.getLogger("Client")

LOSS_RECOVERY_ENABLED = True
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 12000
FILE_TO_SEND = "cat.bmp"  # Replace with a larger file if needed
PACKET_SIZE = 1024
TIMEOUT = 0.01  # Timeout value in seconds
WINDOW_SIZE = 10  # Fixed window size for Go-Back-N


def send_file(simulation_mode, error_rate, loss_recovery=True):
    """
    Reads the file and sends it in packets using the Go-Back-N protocol.
    When loss recovery is enabled, the client uses a sliding window mechanism,
    a timer, and retransmits on timeout.
    When disabled, it sends each packet once.

    Simulation Modes:
      2: Simulate ACK packet bit-errors.
      4: Simulate ACK packet loss.

    Returns a tuple: (client_completion_time, total_retransmissions, throughput in bytes/s).
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if loss_recovery:
        client_socket.setblocking(False)

    start_time = time.time()
    total_retransmissions = 0

    if loss_recovery:
        base = 0
        next_seq = 0
        packets = {}  # Buffer: sequence number -> packet
        timer = None  # Timer for the oldest unacknowledged packet
        file_end = False

        while True:
            # Send new packets if window is not full and file is not finished.
            while next_seq < base + WINDOW_SIZE and not file_end:
                packet = make_packet(FILE_TO_SEND, next_seq, PACKET_SIZE)
                if packet is None:
                    file_end = True
                    break
                client_socket.sendto(packet, (SERVER_ADDRESS, SERVER_PORT))
                logger.debug(f"Packet {next_seq} sent")
                packets[next_seq] = packet
                if base == next_seq:
                    timer = time.time()
                next_seq += 1

            # Check for incoming ACKs.
            try:
                ready = select.select([client_socket], [], [], 0.01)[0]
            except Exception:
                ready = []
            if ready:
                try:
                    ack_data, _ = client_socket.recvfrom(2048)
                    try:
                        correct_ack = int(ack_data.decode())
                    except:
                        correct_ack = -1

                    # For simulation mode 2, simulate ACK bit-error by choosing a random value
                    # in [base, correct_ack - 1] if possible.
                    if simulation_mode == 2 and random.random() < error_rate:
                        logger.debug(f"Simulating ACK bit-error for received ACK {correct_ack}")
                        time.sleep(.002)
                        if correct_ack > base:
                            ack_num = random.randint(base, correct_ack - 1)
                        else:
                            ack_num = -1
                    # For simulation mode 4, simulated ACK error results in the same effect.
                    elif simulation_mode == 4 and random.random() < error_rate:
                        logger.debug(f"Simulating ACK loss for received ACK {correct_ack}")
                        time.sleep(.002)
                        if correct_ack > base:
                            ack_num = random.randint(base, correct_ack - 1)
                        else:
                            ack_num = -1
                    else:
                        ack_num = correct_ack

                    # Process ACK if it's at least the expected base
                    if ack_num >= base:
                        logger.debug(f"ACK {ack_num} received, sliding window")
                        base = ack_num + 1
                        if base == next_seq:
                            timer = None
                        else:
                            timer = time.time()
                    # If the received ACK is less than base, ignore it.
                except Exception as e:
                    logger.debug(f"Error receiving ACK: {e}")

            # Check for timeout on the base packet.
            if timer is not None and (time.time() - timer) > TIMEOUT:
                logger.debug(f"Timeout occurred. Retransmitting packets from {base} to {next_seq - 1}")
                for seq in range(base, next_seq):
                    client_socket.sendto(packets[seq], (SERVER_ADDRESS, SERVER_PORT))
                    total_retransmissions += 1
                timer = time.time()

            if file_end and base == next_seq:
                client_socket.sendto("END".encode(), (SERVER_ADDRESS, SERVER_PORT))
                break
    else:
        # Loss recovery disabled: send each packet once without waiting for ACKs.
        next_seq = 0
        while True:
            packet = make_packet(FILE_TO_SEND, next_seq, PACKET_SIZE)
            if packet is None:
                break
            client_socket.sendto(packet, (SERVER_ADDRESS, SERVER_PORT))
            logger.debug(f"Packet {next_seq} sent (no recovery)")
            next_seq += 1
        client_socket.sendto("END".encode(), (SERVER_ADDRESS, SERVER_PORT))
        total_retransmissions = 0

    end_time = time.time()
    client_socket.close()
    completion_time = end_time - start_time
    file_size = os.path.getsize(FILE_TO_SEND)
    throughput = file_size / completion_time
    logger.debug(
        f"File sent in {completion_time:.2f} seconds with {total_retransmissions} retransmissions. Throughput: {throughput:.2f} bytes/s.")
    return completion_time, total_retransmissions, throughput


def main():
    simulation_mode = 1  # Change mode as needed: 1-5
    error_rate = 0.0
    send_file(simulation_mode, error_rate, loss_recovery=LOSS_RECOVERY_ENABLED)


if __name__ == "__main__":
    main()
