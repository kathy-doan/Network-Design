#!/usr/bin/env python3
"""
run_tests.py - Test harness to run the RDT 2.2 client and server for multiple error rates.
This script coordinates the file transfer for each error rate (from 0% to 60% in 5% increments)
and plots the completion times. Use simulation_mode to select the desired option:
    1: No errors.
    2: Simulated ACK packet bit-errors.
    3: Simulated Data packet bit-errors.
Benjamin Dearden
"""

import threading
import time
import sys
from v2_server import run_server, plot_performance
from v2_client import send_file

# Configuration
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 12000
SIMULATION_MODE = 1  # Set desired simulation mode here: 1, 2, or 3.
ERROR_RATES = [i/100.0 for i in range(0, 65, 5)]  # 0.00, 0.05, ..., 0.60

# Shared variable for performance measurement
completion_times = {}


def run_transfer(error_rate):
    """
    Runs a single file transfer test for the given error_rate.
    Starts the server in a thread and then runs the client.
    The completion time is stored in the completion_times dict.
    """
    # Function to run the server; its run_server returns the transfer time.
    def server_thread():
        nonlocal error_rate
        transfer_time = run_server(SIMULATION_MODE, error_rate)
        completion_times[error_rate] = transfer_time

    # Start server thread
    server = threading.Thread(target=server_thread)
    server.start()

    # Wait briefly to ensure the server is listening
    time.sleep(0.5)

    # Run the client to send the file
    send_file(SIMULATION_MODE, error_rate)

    # Wait for server thread to finish
    server.join()


def main():
    print(f"Starting tests with simulation mode {SIMULATION_MODE}")
    for er in ERROR_RATES:
        print(f"\n--- Testing with error rate {er*100:.0f}% ---")
        run_transfer(er)
        # Small delay between tests
        time.sleep(1)

    # Prepare data for plotting
    error_percentages = [int(er*100) for er in ERROR_RATES]
    times = [completion_times[er] for er in ERROR_RATES]

    # Plot performance
    plot_performance(error_percentages, times, SIMULATION_MODE)

if __name__ == "__main__":
    main()
