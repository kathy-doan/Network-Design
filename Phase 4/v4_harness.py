#!/usr/bin/env python3
"""
Benjamin Dearden
Michael Smith
Peter Dingue
Kathy Doan

v4_harness.py - Test harness to run the Go-Back-N client and server for multiple error rates.
This script coordinates the file transfer for each error rate (from 0% to 60% in 5% increments)
and plots the average completion times, average retransmission counts, and average throughput over several runs.
Simulation Modes:
    1: No errors.
    2: Simulated ACK packet bit-errors.
    3: Simulated DATA packet bit-errors.
    4: Simulated ACK packet loss.
    5: Simulated DATA packet loss.
"""

import threading
import time
import matplotlib.pyplot as plt
import matplotlib
import logging

if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("simulation.log", mode="a"),
            # logging.StreamHandler()
        ]
    )

# Disable noisy loggers from PIL and matplotlib
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)

# Create a logger for the harness
logger = logging.getLogger("Harness")

SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 12000
SIMULATION_MODES = [1, 2, 3, 4, 5]
ERROR_RATES = [i/100.0 for i in range(0, 65, 5)]
TRIALS = 3

mode_labels = {1: "None", 2: "Ack", 3: "Data", 4: "ACK Loss", 5: "Data Loss"}
LOSS_RECOVERY_ENABLED = True

def run_single_transfer(simulation_mode: int, error_rate: float):
    server_completion_time = None
    client_metrics = None

    def server_thread():
        nonlocal server_completion_time
        from v4_server import run_server
        server_completion_time = run_server(simulation_mode, error_rate)

    def client_thread():
        nonlocal client_metrics
        from v4_client import send_file
        client_metrics = send_file(simulation_mode, error_rate, loss_recovery=LOSS_RECOVERY_ENABLED)

    server = threading.Thread(target=server_thread)
    client = threading.Thread(target=client_thread)
    server.start()
    time.sleep(0.5)  # Ensure the server is listening
    client.start()
    client.join()
    server.join()
    return server_completion_time, client_metrics

def main():
    logger.debug("Starting tests for simulation modes: " + str(SIMULATION_MODES))
    all_avg_server_times = {mode: [] for mode in SIMULATION_MODES}
    all_avg_client_times = {mode: [] for mode in SIMULATION_MODES}
    all_avg_retransmissions = {mode: [] for mode in SIMULATION_MODES}
    all_avg_throughput = {mode: [] for mode in SIMULATION_MODES}
    error_percentages = [int(er * 100) for er in ERROR_RATES]

    for mode in SIMULATION_MODES:
        logger.debug(f"\n=== Testing Simulation Mode {mode} ===")
        for er in ERROR_RATES:
            logger.debug(f"  Error rate: {er*100:.0f}%")
            server_times = []
            client_times = []
            retransmissions = []
            throughput_vals = []
            for trial in range(1, TRIALS + 1):
                logger.debug(f"    Run {trial}")
                s_time, client_metrics = run_single_transfer(mode, er)
                server_times.append(s_time)
                client_times.append(client_metrics[0])
                retransmissions.append(client_metrics[1])
                throughput_vals.append(client_metrics[2])
                time.sleep(1)
            avg_server_time = sum(server_times) / len(server_times)
            avg_client_time = sum(client_times) / len(client_times)
            avg_retransmissions = sum(retransmissions) / len(retransmissions)
            avg_throughput = sum(throughput_vals) / len(throughput_vals)
            logger.debug(f"  Average server time at {er*100:.0f}% error: {avg_server_time:.2f} sec")
            logger.debug(f"  Average client time at {er*100:.0f}% error: {avg_client_time:.2f} sec")
            logger.debug(f"  Average retransmissions at {er*100:.0f}% error: {avg_retransmissions:.2f}")
            logger.debug(f"  Average throughput at {er*100:.0f}% error: {avg_throughput:.2f} bytes/s")
            all_avg_server_times[mode].append(avg_server_time)
            all_avg_client_times[mode].append(avg_client_time)
            all_avg_retransmissions[mode].append(avg_retransmissions)
            all_avg_throughput[mode].append(avg_throughput)

    from v4_server import plot_performance
    plot_performance(error_percentages, all_avg_server_times, SIMULATION_MODES, TRIALS)

    plt.figure(figsize=(10, 5))
    for mode in SIMULATION_MODES:
        plt.plot(error_percentages, all_avg_retransmissions[mode], marker='o', label=mode_labels[mode])
    plt.title("Average Retransmissions vs Error Rate")
    plt.xlabel("Error Rate (%)")
    plt.ylabel("Average Retransmissions")
    plt.grid(True)
    plt.legend()
    plt.show()

    plt.figure(figsize=(10, 5))
    for mode in SIMULATION_MODES:
        plt.plot(error_percentages, all_avg_throughput[mode], marker='o', label=mode_labels[mode])
    plt.title("Average Throughput vs Error Rate")
    plt.xlabel("Error Rate (%)")
    plt.ylabel("Throughput (bytes/s)")
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    main()
