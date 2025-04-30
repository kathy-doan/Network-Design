#!/usr/bin/env python3
import socket
import time
import os
import select
import random
import logging
from v5_helpers import make_packet, checksum

random.seed(123)

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
INIT_TIMEOUT = 0.5  # initial RTO in seconds
INIT_CWND = 1
SS_THRESH = 16
MAX_WINDOW_SIZE = 50
ALPHA = 0.125
BETA = 0.25
DUPLICATE_ACK_THRESHOLD = 3

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
            logger.warning(f"Unexpected response during teardown: '{response}'")
    except socket.timeout:
        logger.warning("Timeout waiting for server ACK during teardown")


def send_file(simulation_mode, error_rate, file_name="cat.jpeg",
              initial_timeout=None, initial_cwnd=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if not tcp_handshake(sock):
        sock.close()
        return 0, 0, 0, [], [], []

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

    # History data for plotting
    cwnd_history = []
    rtt_history = []
    rto_history = []

    # For TCP Reno
    duplicate_acks = {}
    fast_recovery = False

    start_time = time.time()
    file_end = False

    # Record initial values
    cwnd_history.append((0, cwnd))
    rto_history.append((0, rto))

    while not file_end or base != next_seq:
        # Record cwnd at this point in time
        cwnd_history.append((time.time() - start_time, cwnd))

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

                # Check for duplicate ACKs (TCP Reno)
                if ack == base - 1:
                    duplicate_acks[ack] = duplicate_acks.get(ack, 0) + 1

                    # Fast Retransmit and Fast Recovery
                    if duplicate_acks[ack] == DUPLICATE_ACK_THRESHOLD:
                        logger.warning(f"Triple duplicate ACK for {ack}, triggering Fast Retransmit")
                        if base in packets:
                            sock.sendto(packets[base][0], (SERVER_ADDRESS, SERVER_PORT))
                            retransmissions += 1

                            # TCP Reno Fast Recovery
                            ssthresh = max(int(cwnd / 2), 2)
                            cwnd = ssthresh + 3  # Inflated by duplicate ACKs
                            fast_recovery = True
                            logger.debug(f"Fast Recovery: cwnd={cwnd}, ssthresh={ssthresh}")

                    elif duplicate_acks[ack] > DUPLICATE_ACK_THRESHOLD and fast_recovery:
                        # For each additional duplicate ACK, increase cwnd by 1
                        cwnd += 1
                        logger.debug(f"Fast Recovery inflation: cwnd={cwnd}")

                elif ack >= base and ack in packets:
                    # Reset duplicate ACK counter for new ACKs
                    duplicate_acks.clear()

                    # If exiting fast recovery
                    if fast_recovery:
                        cwnd = ssthresh
                        fast_recovery = False
                        logger.debug(f"Exiting Fast Recovery: cwnd={cwnd}")

                    # Calculate RTT and update RTO
                    sample_rtt = time.time() - packets[ack][1]
                    rtt_history.append((time.time() - start_time, sample_rtt))

                    if estimated_rtt is None:
                        estimated_rtt = sample_rtt
                    else:
                        estimated_rtt = (1 - ALPHA) * estimated_rtt + ALPHA * sample_rtt
                        dev_rtt = (1 - BETA) * dev_rtt + BETA * abs(sample_rtt - estimated_rtt)
                    rto = estimated_rtt + 4 * dev_rtt
                    rto_history.append((time.time() - start_time, rto))

                    logger.debug(f"ACK {ack} received. Updating cwnd and base. RTT={sample_rtt:.4f}s, RTO={rto:.4f}s")

                    # Normal cwnd update
                    if not fast_recovery:
                        if cwnd < ssthresh:
                            cwnd += 1  # Slow start
                            logger.debug(f"Slow Start: cwnd={cwnd}")
                        else:
                            cwnd += 1 / cwnd  # Congestion avoidance
                            logger.debug(f"Congestion Avoidance: cwnd={cwnd}")

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
            cwnd = 1  # TCP Tahoe behavior (reset to 1)
            logger.debug(f"Timeout: cwnd={cwnd}, ssthresh={ssthresh}")

            # Record the window change due to timeout
            cwnd_history.append((time.time() - start_time, cwnd))

            for seq in range(base, next_seq):
                if seq in packets:
                    sock.sendto(packets[seq][0], (SERVER_ADDRESS, SERVER_PORT))
                    packets[seq] = (packets[seq][0], time.time())
                    retransmissions += 1
            timer = time.time()

    sock.sendto("END".encode(), (SERVER_ADDRESS, SERVER_PORT))
    tcp_teardown(sock)
    sock.close()

    duration = time.time() - start_time
    throughput = os.path.getsize(file_name) / duration

    logger.info(f"Transfer completed in {duration:.2f}s, {retransmissions} retransmissions, {throughput:.2f} bytes/s")

    return duration, retransmissions, throughput, cwnd_history, rtt_history, rto_history


def main():
    simulation_mode = 1
    error_rate = 0.0

    # Run a single file transfer with data collection
    duration, retransmissions, throughput, cwnd_history, rtt_history, rto_history = send_file(simulation_mode,
                                                                                              error_rate)

    # Generate plots from collected data
    import matplotlib.pyplot as plt

    # Plot 1: Congestion Window Size vs Time
    plt.figure(figsize=(10, 6))
    times, cwnd_values = zip(*cwnd_history)
    plt.plot(times, cwnd_values, 'b-', marker='o', markersize=3)
    plt.title('Congestion Window Size vs Time')
    plt.xlabel('Time (seconds)')
    plt.ylabel('cwnd (segments)')
    plt.grid(True)
    plt.savefig('cwnd_vs_time.png')

    # Plot 2: Sample RTT vs Time
    if rtt_history:
        plt.figure(figsize=(10, 6))
        times, rtt_values = zip(*rtt_history)
        plt.plot(times, rtt_values, 'g-', marker='o', markersize=3)
        plt.title('Sample RTT vs Time')
        plt.xlabel('Time (seconds)')
        plt.ylabel('RTT (seconds)')
        plt.grid(True)
        plt.savefig('rtt_vs_time.png')

    # Plot 3: RTO vs Time
    if rto_history:
        plt.figure(figsize=(10, 6))
        times, rto_values = zip(*rto_history)
        plt.plot(times, rto_values, 'r-', marker='o', markersize=3)
        plt.title('RTO vs Time')
        plt.xlabel('Time (seconds)')
        plt.ylabel('RTO (seconds)')
        plt.grid(True)
        plt.savefig('rto_vs_time.png')

    plt.show()


if __name__ == "__main__":
    main()