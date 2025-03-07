#!/usr/bin/env python3
"""
run_tests.py - Test harness for RDT 2.2 client and server.
This script tests three simulation modes:
    Mode 1 (None): No errors.
    Mode 2 (Ack): Simulated ACK bit-errors.
    Mode 3 (Data): Simulated Data bit-errors.
It plots the average completion times for each mode across error rates (0% to 60% in 5% increments).
"""

import threading
import time

import matplotlib.pyplot as plt
from v2_1_server import plot_performance
from v2_1_client import send_file

DEBUG = True

def debug_print(msg):
    if DEBUG:
        print(msg)

SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 12000
SIMULATION_MODES = [1, 2, 3]  # Modes: None, Ack, Data
ERROR_RATES = [i/100.0 for i in range(0, 65, 5)]
TRIALS = 3

def run_single_transfer(simulation_mode, error_rate):
    """
    Runs a single file transfer test for the given simulation_mode and error_rate.
    Starts the server in a thread and then runs the client.
    Returns the completion time for the transfer.
    """
    completion_time = None

    def server_thread():
        nonlocal completion_time, error_rate, simulation_mode
        from v2_1_server import run_server
        completion_time = run_server(simulation_mode, error_rate)

    from v2_1_server import run_server
    server = threading.Thread(target=server_thread)
    server.start()

    time.sleep(0.5)
    send_file(simulation_mode, error_rate)
    server.join()
    return completion_time

def main():
    debug_print("Starting tests for simulation modes: " + str(SIMULATION_MODES))
    all_avg_times = {mode: [] for mode in SIMULATION_MODES}
    error_percentages = [int(er * 100) for er in ERROR_RATES]

    for mode in SIMULATION_MODES:
        debug_print(f"\n=== Testing Simulation Mode {mode} ===")
        for er in ERROR_RATES:
            trial_times = []
            debug_print(f"  Error rate: {er*100:.0f}%")
            for trial in range(1, TRIALS + 1):
                debug_print(f"    Run {trial}")
                t_time = run_single_transfer(mode, er)
                trial_times.append(t_time)
                time.sleep(1)
            avg_time = sum(trial_times) / len(trial_times)
            debug_print(f"  Average completion time at {er*100:.0f}% error: {avg_time:.2f} seconds")
            all_avg_times[mode].append(avg_time)

    plot_performance(error_percentages, all_avg_times, SIMULATION_MODES, TRIALS)

if __name__ == "__main__":
    main()
