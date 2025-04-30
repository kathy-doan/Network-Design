#!/usr/bin/env python3
import socket
import time
import os
import select
import random
import logging
import csv
from v5_helpers import make_packet, checksum

# Logging Setup
ENABLE_CONSOLE_LOG = True
log_handlers = [logging.FileHandler("tcp_simulation.log", mode="a")]
if ENABLE_CONSOLE_LOG:
    log_handlers.append(logging.StreamHandler())
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [CLIENT] %(message)s',
                    handlers=log_handlers)
logger = logging.getLogger("Client")

# Constants
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 12000
PACKET_SIZE = 1024
INIT_TIMEOUT = 0.5   # initial RTO in seconds
INIT_CWND = 1
SS_THRESH = 16
MAX_WINDOW_SIZE = 50
ALPHA = 0.125
BETA = 0.25

# TCP Control Flags
SYN = "SYN"
SYN_ACK = "SYN-ACK"
ACK = "ACK"
FIN = "FIN"

def tcp_handshake(sock):
    sock.settimeout(2)
    logger.info("Starting 3-way handshake")
    sock.sendto(SYN.encode(), (SERVER_ADDRESS, SERVER_PORT))
    try:
        data, _ = sock.recvfrom(1024)
        if data.decode() == SYN_ACK:
            sock.sendto(ACK.encode(), (SERVER_ADDRESS, SERVER_PORT))
            logger.info("Handshake complete")
            return True
    except socket.timeout:
        logger.warning("Handshake failed")
    return False

def tcp_teardown(sock):
    logger.info("Starting connection teardown")
    sock.settimeout(2)

    try:
        sock.sendto(FIN.encode(), (SERVER_ADDRESS, SERVER_PORT))
        data, _ = sock.recvfrom(1024)
        response = data.decode(errors='ignore').strip()
        if response == ACK:
            logger.info("Teardown acknowledged by server")
        else:
            logger.warning("Unexpected response during teardown: '{response}'")
    except socket.timeout:
        logger.warning("Timeout waiting for server ACK during teardown")

def send_file(simulation_mode, error_rate, file_name="cat.jpeg",
              initial_timeout=None, initial_cwnd=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if not tcp_handshake(sock):
        sock.close()
        return 0, 0, 0

    base = 0
    next_seq = 0
    cwnd = initial_cwnd if initial_cwnd else INIT_CWND
    ssthresh = SS_THRESH
    timer = None
    packets = {}
    rto = initial_timeout if initial_timeout else INIT_TIMEOUT
    estimated_rtt = None
    dev_rtt = 0
    retransmissions = 0
    start_time = time.time()
    file_end = False

    # Tracking lists for plotting
    timestamps = []
    cwnd_list = []
    rtt_list = []
    rto_list = []

    while not file_end or base != next_seq:
        # Send packets within cwnd
        while next_seq < base + cwnd and not file_end:
            packet = make_packet(file_name, next_seq, PACKET_SIZE)
            if packet is None:
                file_end = True
                break
            sock.sendto(packet, (SERVER_ADDRESS, SERVER_PORT))
            packets[next_seq] = (packet, time.time())
            if base == next_seq:
                timer = time.time()
            logger.debug(f"Sent packet {next_seq}")
            next_seq += 1

        # Wait for ACK
        sock.settimeout(0.01)
        try:
            ack_data, _ = sock.recvfrom(2048)
            ack_str = ack_data.decode(errors='ignore')

            if simulation_mode == 2 and random.random() < error_rate:
                logger.warning("Simulating ACK bit - error")
                ack_str = str(random.randint(0, max(0, base - 1)))

            if simulation_mode == 4 and random.random() < error_rate:
                logger.warning("Simulating ACK loss error (skipping this ACK)")
                continue

            if ack_str.isdigit():
                ack = int(ack_str)
                if ack >= base and ack in packets:
                    sample_rtt = time.time() - packets[ack][1]
                    if estimated_rtt is None:
                        estimated_rtt = sample_rtt
                    else:
                        estimated_rtt = (1 - ALPHA) * estimated_rtt + ALPHA * sample_rtt
                        dev_rtt = (1 - BETA) * dev_rtt + BETA * abs(sample_rtt - estimated_rtt)
                    rto = estimated_rtt + 4 * dev_rtt

                    # Log metrics
                    timestamps.append(time.time() - start_time)
                    cwnd_list.append(cwnd)
                    rtt_list.append(sample_rtt)
                    rto_list.append(rto)

                    logger.debug(f"ACK {ack} received. Updating cwnd and base")

                    if cwnd < ssthresh:
                        cwnd += 1
                    else:
                        cwnd += 1 / cwnd

                    base = ack + 1
                    timer = time.time() if base != next_seq else None
                    for seq in list(packets):
                        if seq <= ack:
                            del packets[seq]
        except socket.timeout:
            pass

        if timer and time.time() - timer > rto:
            logger.warning(f"Timeout: retransmitting from {base}")
            ssthresh = max(int(cwnd / 2), 1)
            cwnd = 1
            for seq in range(base, next_seq):
                sock.sendto(packets[seq][0], (SERVER_ADDRESS, SERVER_PORT))
                packets[seq] = (packets[seq][0], time.time())
                retransmissions += 1
            timer = time.time()

    sock.sendto("END".encode(), (SERVER_ADDRESS, SERVER_PORT))
    tcp_teardown(sock)
    sock.close()

    duration = time.time() - start_time
    throughput = os.path.getsize(file_name) / duration

    # Save plot data
    metrics_file = f"metrics_mode{simulation_mode}_err{int(error_rate*100)}.csv"
    with open(metrics_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "CWND", "SampleRTT", "RTO"])
        for row in zip(timestamps, cwnd_list, rtt_list, rto_list):
            writer.writerow(row)

    return duration, retransmissions, throughput

def main():
    simulation_mode = 1
    error_rate = 0.0
    send_file(simulation_mode, error_rate)

if __name__ == "__main__":
    main()
