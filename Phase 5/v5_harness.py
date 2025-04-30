#!/usr/bin/env python3
import threading
import time
import logging
import os
import gc
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
from v5_server import run_server
from v5_client import send_file

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
)

logger = logging.getLogger("Harness")
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

# --- CONFIGURATION ---

SIMULATION_MODES = [1, 2, 3, 4, 5]
ERROR_RATES = [i / 100.0 for i in range(0, 65, 5)]  # 0% to 60% in 5% steps
TIMEOUT_VALUES = [i / 1000.0 for i in range(10, 110, 10)]  # 10ms to 100ms
WINDOW_SIZES = [1, 2, 5, 10, 20, 30, 40, 50]
TRIALS = 3  # Number of trials
FILENAME = "kitty.png"  # Make sure this file exists in directory
TEST_ERROR_RATE = 0.2  # Fixed error rate for timeout and window tests
PLOTS_DIR = "plots"
# ----------------------

# Create plots directory if it doesn't exist
os.makedirs(PLOTS_DIR, exist_ok=True)


def run_single_transfer(mode, error_rate, initial_timeout=None, initial_cwnd=None):
    """
    Run a single file transfer simulation with server and client threads.
    Returns data necessary for plotting.
    """
    server_time = None
    client_time = None
    retrans = None
    throughput = None
    cwnd_history = None
    rtt_history = None
    rto_history = None

    def server_thr():
        nonlocal server_time
        try:
            server_time = run_server(mode, error_rate)
        except Exception as e:
            logger.error(f"Server thread error: {e}")
            server_time = 0

    def client_thr():
        nonlocal client_time, retrans, throughput, cwnd_history, rtt_history, rto_history
        try:
            results = send_file(
                mode,
                error_rate,
                file_name=FILENAME,
                initial_timeout=initial_timeout,
                initial_cwnd=initial_cwnd
            )

            client_time = results[0]
            retrans = results[1]
            throughput = results[2]

            # Handle the case where we don't receive history data
            if len(results) > 3:
                cwnd_history = results[3]
            else:
                cwnd_history = []

            if len(results) > 4:
                rtt_history = results[4]
            else:
                rtt_history = []

            if len(results) > 5:
                rto_history = results[5]
            else:
                rto_history = []

        except Exception as e:
            logger.error(f"Client thread error: {e}")
            client_time = 0
            retrans = 0
            throughput = 0
            cwnd_history = []
            rtt_history = []
            rto_history = []

    # Start server thread
    t_s = threading.Thread(target=server_thr)
    t_s.daemon = True  # Set as daemon to ensure it terminates with main program
    t_s.start()
    time.sleep(0.5)  # give server a moment to bind()

    # Start client thread
    t_c = threading.Thread(target=client_thr)
    t_c.daemon = True  # Set as daemon
    t_c.start()

    # Wait for completion with timeout
    try:
        t_c.join(timeout=120)  # 2-minute timeout for client
        if t_c.is_alive():
            logger.warning(f"Client thread timeout for mode {mode}, error {error_rate}")
            return 0, 0, 0, [], [], []

        t_s.join(timeout=5)  # Short timeout for server
    except Exception as e:
        logger.error(f"Thread join error: {e}")

    # Force garbage collection to prevent memory leaks
    gc.collect()

    # Add small delay to ensure sockets are closed
    time.sleep(1)

    return server_time, client_time, retrans, throughput, cwnd_history, rtt_history, rto_history


def plot_dynamics_vs_time(cwnd_history, rtt_history, rto_history, scenario_name="default"):
    """Generate the three time-based plots required for TCP analysis"""
    try:
        # Plot 1: Congestion Window Size vs Time
        plt.figure(figsize=(10, 6))
        if cwnd_history and len(cwnd_history) > 0:
            times, cwnd = zip(*cwnd_history)
            plt.plot(times, cwnd, 'b-', marker='o', markersize=3)
        plt.title('Congestion Window Size vs Time')
        plt.xlabel('Time (seconds)')
        plt.ylabel('cwnd (segments)')
        plt.grid(True)
        plt.savefig(f'{PLOTS_DIR}/cwnd_vs_time_{scenario_name}.png')
        plt.close()

        # Plot 2: Sample RTT vs Time
        plt.figure(figsize=(10, 6))
        if rtt_history and len(rtt_history) > 0:
            times, rtts = zip(*rtt_history)
            plt.plot(times, rtts, 'g-', marker='o', markersize=3)
        plt.title('Sample RTT vs Time')
        plt.xlabel('Time (seconds)')
        plt.ylabel('RTT (seconds)')
        plt.grid(True)
        plt.savefig(f'{PLOTS_DIR}/rtt_vs_time_{scenario_name}.png')
        plt.close()

        # Plot 3: RTO vs Time
        plt.figure(figsize=(10, 6))
        if rto_history and len(rto_history) > 0:
            times, rtos = zip(*rto_history)
            plt.plot(times, rtos, 'r-', marker='o', markersize=3)
        plt.title('RTO vs Time')
        plt.xlabel('Time (seconds)')
        plt.ylabel('RTO (seconds)')
        plt.grid(True)
        plt.savefig(f'{PLOTS_DIR}/rto_vs_time_{scenario_name}.png')
        plt.close()

        logger.info(f"Generated dynamic plots for scenario: {scenario_name}")
    except Exception as e:
        logger.error(f"Error creating plots for {scenario_name}: {e}")


def run_error_rate_test():
    """Test impact of different error/loss rates"""
    logger.info("=== Running Error Rate Impact Test ===")

    completion_times = {mode: [] for mode in SIMULATION_MODES}

    for mode in SIMULATION_MODES:
        for error_rate in ERROR_RATES:
            cumulative_time = 0
            successful_trials = 0

            for trial in range(TRIALS):
                logger.info(f"Mode {mode} - Error Rate {error_rate * 100}% - Trial {trial + 1}")

                try:
                    _, client_time, _, _, cwnd_h, rtt_h, rto_h = run_single_transfer(mode, error_rate)

                    # Only count successful transfers
                    if client_time > 0:
                        # Save detailed plots for a specific error rate (e.g., 20%)
                        if abs(error_rate - 0.2) < 0.01 and trial == 0:
                            plot_dynamics_vs_time(cwnd_h, rtt_h, rto_h, f"mode{mode}_error{int(error_rate * 100)}")

                        cumulative_time += client_time
                        successful_trials += 1
                except Exception as e:
                    logger.error(f"Error in trial: {e}")

                # Clear memory between trials
                plt.close('all')
                gc.collect()
                time.sleep(1)  # Pause between trials

            # Calculate average time from successful trials
            avg_time = cumulative_time / max(successful_trials, 1)  # Avoid division by zero
            completion_times[mode].append(avg_time)
            logger.info(f"Average completion time: {avg_time:.3f}s")

    # Generate the comparison plot
    try:
        plt.figure(figsize=(12, 8))
        for mode in SIMULATION_MODES:
            plt.plot(
                [er * 100 for er in ERROR_RATES],
                completion_times[mode],
                marker='o',
                label=f"Mode {mode}"
            )

        plt.title('Completion Time vs Loss/Error Rate')
        plt.xlabel('Loss/Error Rate (%)')
        plt.ylabel('Completion Time (seconds)')
        plt.grid(True)
        plt.legend()
        plt.savefig(f'{PLOTS_DIR}/completion_vs_errorrate.png')
        plt.close()
    except Exception as e:
        logger.error(f"Error creating error rate plot: {e}")

    return completion_times


def run_timeout_value_test():
    """Test impact of different timeout values"""
    logger.info("=== Running Timeout Value Impact Test ===")

    completion_times = []

    # Choose a specific mode and error rate for this test
    mode = 1  # Normal mode
    error_rate = TEST_ERROR_RATE  # Fixed error rate (e.g., 20%)

    for timeout in TIMEOUT_VALUES:
        cumulative_time = 0
        successful_trials = 0

        for trial in range(TRIALS):
            logger.info(f"Timeout {timeout * 1000}ms - Trial {trial + 1}")

            try:
                _, client_time, _, _, cwnd_h, rtt_h, rto_h = run_single_transfer(
                    mode,
                    error_rate,
                    initial_timeout=timeout
                )

                if client_time > 0:
                    # Save detailed plots for a specific timeout value
                    if abs(timeout - 0.05) < 0.01 and trial == 0:
                        plot_dynamics_vs_time(cwnd_h, rtt_h, rto_h, f"timeout{int(timeout * 1000)}")

                    cumulative_time += client_time
                    successful_trials += 1
            except Exception as e:
                logger.error(f"Error in timeout trial: {e}")

            # Clear memory between trials
            plt.close('all')
            gc.collect()
            time.sleep(1)

        # Calculate average from successful trials
        avg_time = cumulative_time / max(successful_trials, 1)
        completion_times.append(avg_time)
        logger.info(f"Average completion time: {avg_time:.3f}s")

    # Generate the comparison plot
    try:
        plt.figure(figsize=(10, 6))
        plt.plot(
            [t * 1000 for t in TIMEOUT_VALUES],  # Convert to ms for display
            completion_times,
            marker='o'
        )

        plt.title(f'Completion Time vs Timeout Value (Error Rate: {TEST_ERROR_RATE * 100}%)')
        plt.xlabel('Timeout Value (ms)')
        plt.ylabel('Completion Time (seconds)')
        plt.grid(True)
        plt.savefig(f'{PLOTS_DIR}/completion_vs_timeout.png')
        plt.close()
    except Exception as e:
        logger.error(f"Error creating timeout plot: {e}")

    return completion_times


def run_window_size_test():
    """Test impact of different window sizes"""
    logger.info("=== Running Window Size Impact Test ===")

    completion_times = []

    # Choose a specific mode and error rate for this test
    mode = 1  # Normal mode
    error_rate = TEST_ERROR_RATE  # Fixed error rate (e.g., 20%)

    for window in WINDOW_SIZES:
        cumulative_time = 0
        successful_trials = 0

        for trial in range(TRIALS):
            logger.info(f"Window Size {window} - Trial {trial + 1}")

            try:
                _, client_time, _, _, cwnd_h, rtt_h, rto_h = run_single_transfer(
                    mode,
                    error_rate,
                    initial_cwnd=window
                )

                if client_time > 0:
                    # Save detailed plots for a specific window size
                    if window == 10 and trial == 0:
                        plot_dynamics_vs_time(cwnd_h, rtt_h, rto_h, f"window{window}")

                    cumulative_time += client_time
                    successful_trials += 1
            except Exception as e:
                logger.error(f"Error in window size trial: {e}")

            # Clear memory between trials
            plt.close('all')
            gc.collect()
            time.sleep(1)

        # Calculate average from successful trials
        avg_time = cumulative_time / max(successful_trials, 1)
        completion_times.append(avg_time)
        logger.info(f"Average completion time: {avg_time:.3f}s")

    # Generate the comparison plot
    try:
        plt.figure(figsize=(10, 6))
        plt.plot(
            WINDOW_SIZES,
            completion_times,
            marker='o'
        )

        plt.title(f'Completion Time vs Window Size (Error Rate: {TEST_ERROR_RATE * 100}%)')
        plt.xlabel('Window Size (segments)')
        plt.ylabel('Completion Time (seconds)')
        plt.grid(True)
        plt.savefig(f'{PLOTS_DIR}/completion_vs_windowsize.png')
        plt.close()
    except Exception as e:
        logger.error(f"Error creating window size plot: {e}")

    return completion_times


def compare_protocols(error_rate_results):
    """Create a comparison plot between different protocols/modes"""
    # Sample data point - use error rate of 20%
    try:
        error_index = next((i for i, er in enumerate(ERROR_RATES) if abs(er - 0.2) < 0.01), 0)

        protocol_names = ["Stop-and-Wait", "GBN", "SR", "TCP Tahoe", "TCP Reno"]
        completion_times = [error_rate_results[mode][error_index] for mode in SIMULATION_MODES]

        plt.figure(figsize=(10, 6))
        bars = plt.bar(protocol_names, completion_times)

        # Add values on top of the bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                     f'{height:.2f}s',
                     ha='center', va='bottom')

        plt.title(f'Protocol Performance Comparison (Error Rate: {TEST_ERROR_RATE * 100}%)')
        plt.xlabel('Protocol')
        plt.ylabel('Completion Time (seconds)')
        plt.grid(True, axis='y')
        plt.savefig(f'{PLOTS_DIR}/protocol_comparison.png')
        plt.close()
    except Exception as e:
        logger.error(f"Error creating protocol comparison plot: {e}")


def main():
    logger.info("Starting TCP performance testing harness")

    try:
        # Run test modules individually
        # This allows partial results even if one test fails
        error_rate_results = None

        try:
            error_rate_results = run_error_rate_test()
        except Exception as e:
            logger.error(f"Error rate test failed: {e}")

        try:
            run_timeout_value_test()
        except Exception as e:
            logger.error(f"Timeout test failed: {e}")

        try:
            run_window_size_test()
        except Exception as e:
            logger.error(f"Window size test failed: {e}")

        # Only run protocol comparison if we have error rate results
        if error_rate_results:
            try:
                compare_protocols(error_rate_results)
            except Exception as e:
                logger.error(f"Protocol comparison failed: {e}")

    except Exception as e:
        logger.error(f"Critical error in main: {e}")
    finally:
        # Clean up resources
        plt.close('all')
        gc.collect()

    logger.info("All tests completed. Plots saved to 'plots' directory.")


if __name__ == "__main__":
    main()