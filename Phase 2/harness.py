#!/usr/bin/env python3
"""
run_tests.py - Test harness to run the RDT 2.2 client and server for multiple error rates.
This script coordinates the file transfer for each error rate (from 0% to 60% in 5% increments)
and plots the average completion times over 3 runs. Use simulation_mode to select the desired option:
    1: No errors.
    2: Simulated ACK packet bit-errors.
    3: Simulated Data packet bit-errors.
Benjamin Dearden
"""

import threading
import time
from v2_server import run_server, plot_performance
from v2_client import send_file

DEBUG = False  # Set to True to enable debug output

def debug_print(msg):
    if DEBUG:
        print(msg)

# Configuration
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 12000
SIMULATION_MODE = 1  # Set desired simulation mode here: 1, 2, or 3.
ERROR_RATES = [i/100.0 for i in range(0, 65, 5)]  # 0.00, 0.05, ..., 0.60
TRIALS = 3  # Number of runs per error rate

def run_single_transfer(error_rate):
    """
    Runs a single file transfer test for the given error_rate.
    Starts the server in a thread and then runs the client.
    Returns the completion time for the transfer.
    """
    completion_time = None

    def server_thread():
        nonlocal completion_time, error_rate
        completion_time = run_server(SIMULATION_MODE, error_rate)

    # Start server thread
    server = threading.Thread(target=server_thread)
    server.start()

    # Wait briefly to ensure the server is listening
    time.sleep(0.5)

    # Run the client to send the file
    send_file(SIMULATION_MODE, error_rate)

    # Wait for server thread to finish
    server.join()
    return completion_time

def main():
    debug_print(f"Starting tests with simulation mode {SIMULATION_MODE}")
    avg_completion_times = {}
    for er in ERROR_RATES:
        trial_times = []
        debug_print(f"\n--- Testing with error rate {er*100:.0f}% ---")
        for trial in range(1, TRIALS + 1):
            debug_print(f"Run {trial} for error rate {er*100:.0f}%")
            t_time = run_single_transfer(er)
            trial_times.append(t_time)
            # Small delay between trials
            time.sleep(1)
        avg_time = sum(trial_times) / len(trial_times)
        avg_completion_times[er] = avg_time
        debug_print(f"Average completion time for error rate {er*100:.0f}%: {avg_time:.2f} seconds")

    # Prepare data for plotting
    error_percentages = [int(er*100) for er in ERROR_RATES]
    times = [avg_completion_times[er] for er in ERROR_RATES]

    # Plot performance (this output is always visible)
    plot_performance(error_percentages, times, SIMULATION_MODE, TRIALS)

if __name__ == "__main__":
    main()
