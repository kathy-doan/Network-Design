"""
Benjamin Dearden
Michael Smith
Peter Dingue
Kathy Doan
4/30/25
v5_harness.py for Phase 5 EECE 4830 Project
This harness takes the client and server files and runs them through extensive
tests to produce output plots. The code used here was taken from previous phase and
modified as needed.

"""

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
from v5_client import send_file, PROTOCOL_SLOW_START_ONLY, PROTOCOL_AIMD_ONLY, PROTOCOL_TAHOE, PROTOCOL_RENO

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
)

logger = logging.getLogger("Harness")
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

# --- CONFIGURATION ---

# Error simulation modes with descriptive names
SIMULATION_MODE_NAMES = {
    1: "Normal",
    2: "ACK Bit Error",
    3: "Packet Corruption",
    4: "ACK Loss",
    5: "Packet Loss"
}

# Protocol names for better readability
PROTOCOL_NAMES = {
    PROTOCOL_SLOW_START_ONLY: "Slow Start Only",
    PROTOCOL_AIMD_ONLY: "AIMD Only",
    PROTOCOL_TAHOE: "TCP Tahoe",
    PROTOCOL_RENO: "TCP Reno"
}

# Define the simulation modes and protocols to test
SIMULATION_MODES = [1, 2, 3, 4, 5]  # Keep all simulation modes
CONGESTION_PROTOCOLS = [PROTOCOL_SLOW_START_ONLY, PROTOCOL_AIMD_ONLY, PROTOCOL_TAHOE, PROTOCOL_RENO]
ERROR_RATES = [i / 100.0 for i in range(0, 65, 5)]  # 0% to 60% in 5% steps
TIMEOUT_VALUES = [i / 1000.0 for i in range(10, 110, 10)]  # 10ms to 100ms in 10ms steps
WINDOW_SIZES = [1, 2, 5, 10, 20, 30, 40, 50]  # Window sizes from 1 to 50
TRIALS = 3  # Number of trials
FILENAME = "kitty.png"  # Make sure this file exists in directory
TEST_ERROR_RATE = 0.2  # Fixed error rate for timeout and window tests
PLOTS_DIR = "plots"
# ----------------------

# Create plots directory if it doesn't exist
os.makedirs(PLOTS_DIR, exist_ok=True)


def run_single_transfer(mode, error_rate, congestion_protocol, initial_timeout=None, initial_cwnd=None):
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
                congestion_protocol,
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
            logger.warning(
                f"Client thread timeout for mode {SIMULATION_MODE_NAMES[mode]}, protocol {PROTOCOL_NAMES[congestion_protocol]}, error {error_rate}")
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


def run_error_simulation_mode_test():
    """Test impact of different error simulation modes across different congestion control protocols"""
    logger.info("=== Running Error Simulation Mode Test ===")

    # Structure to hold results for each protocol and mode
    completion_times = {protocol: {mode: 0 for mode in SIMULATION_MODES} for protocol in CONGESTION_PROTOCOLS}
    retransmissions = {protocol: {mode: 0 for mode in SIMULATION_MODES} for protocol in CONGESTION_PROTOCOLS}
    throughputs = {protocol: {mode: 0 for mode in SIMULATION_MODES} for protocol in CONGESTION_PROTOCOLS}

    # Fixed error rate for this test
    error_rate = TEST_ERROR_RATE

    for protocol in CONGESTION_PROTOCOLS:
        for mode in SIMULATION_MODES:
            cumulative_time = 0
            cumulative_retrans = 0
            cumulative_throughput = 0
            successful_trials = 0

            for trial in range(TRIALS):
                logger.info(
                    f"Protocol {PROTOCOL_NAMES[protocol]} - Mode {SIMULATION_MODE_NAMES[mode]} - Trial {trial + 1}")

                try:
                    _, client_time, retrans, throughput, cwnd_h, rtt_h, rto_h = run_single_transfer(mode, error_rate,
                                                                                                    protocol)

                    # Only count successful transfers
                    if client_time > 0:
                        # Save detailed plots for trial 0
                        if trial == 0:
                            plot_dynamics_vs_time(cwnd_h, rtt_h, rto_h, f"protocol{protocol}_mode{mode}")

                        cumulative_time += client_time
                        cumulative_retrans += retrans
                        cumulative_throughput += throughput
                        successful_trials += 1
                except Exception as e:
                    logger.error(f"Error in trial: {e}")

                # Clear memory between trials
                plt.close('all')
                gc.collect()
                time.sleep(1)  # Pause between trials

            # Calculate averages from successful trials
            if successful_trials > 0:
                completion_times[protocol][mode] = cumulative_time / successful_trials
                retransmissions[protocol][mode] = cumulative_retrans / successful_trials
                throughputs[protocol][mode] = cumulative_throughput / successful_trials
                logger.info(f"Average completion time: {completion_times[protocol][mode]:.3f}s")
            else:
                completion_times[protocol][mode] = 0
                retransmissions[protocol][mode] = 0
                throughputs[protocol][mode] = 0
                logger.info("No successful trials")

    # Generate the comparison plot for completion times
    try:
        plt.figure(figsize=(14, 8))

        # Set width of bars
        barWidth = 0.2

        # Set positions for bars
        r = np.arange(len(SIMULATION_MODES))

        # Create bars for each protocol
        for i, protocol in enumerate(CONGESTION_PROTOCOLS):
            plt.bar(
                [x + i * barWidth for x in r],
                [completion_times[protocol][mode] for mode in SIMULATION_MODES],
                width=barWidth,
                label=PROTOCOL_NAMES[protocol]
            )

        # Add labels and title
        plt.xlabel('Error Simulation Mode')
        plt.ylabel('Completion Time (seconds)')
        plt.title(f'Protocol Performance Across Error Simulation Modes (Error Rate: {TEST_ERROR_RATE * 100}%)')

        # Add x-axis ticks
        plt.xticks([r + barWidth * 1.5 for r in range(len(SIMULATION_MODES))],
                   [SIMULATION_MODE_NAMES[mode] for mode in SIMULATION_MODES])

        # Add legend
        plt.legend()

        # Save plot
        plt.grid(True, axis='y')
        plt.tight_layout()
        plt.savefig(f'{PLOTS_DIR}/protocol_vs_error_mode_completion.png')
        plt.close()

        # Similar plot for retransmissions
        plt.figure(figsize=(14, 8))
        for i, protocol in enumerate(CONGESTION_PROTOCOLS):
            plt.bar(
                [x + i * barWidth for x in r],
                [retransmissions[protocol][mode] for mode in SIMULATION_MODES],
                width=barWidth,
                label=PROTOCOL_NAMES[protocol]
            )

        plt.xlabel('Error Simulation Mode')
        plt.ylabel('Number of Retransmissions')
        plt.title(f'Protocol Retransmissions Across Error Simulation Modes (Error Rate: {TEST_ERROR_RATE * 100}%)')
        plt.xticks([r + barWidth * 1.5 for r in range(len(SIMULATION_MODES))],
                   [SIMULATION_MODE_NAMES[mode] for mode in SIMULATION_MODES])
        plt.legend()
        plt.grid(True, axis='y')
        plt.tight_layout()
        plt.savefig(f'{PLOTS_DIR}/protocol_vs_error_mode_retransmissions.png')
        plt.close()

        # Similar plot for throughput
        plt.figure(figsize=(14, 8))
        for i, protocol in enumerate(CONGESTION_PROTOCOLS):
            plt.bar(
                [x + i * barWidth for x in r],
                [throughputs[protocol][mode] for mode in SIMULATION_MODES],
                width=barWidth,
                label=PROTOCOL_NAMES[protocol]
            )

        plt.xlabel('Error Simulation Mode')
        plt.ylabel('Throughput (bytes/second)')
        plt.title(f'Protocol Throughput Across Error Simulation Modes (Error Rate: {TEST_ERROR_RATE * 100}%)')
        plt.xticks([r + barWidth * 1.5 for r in range(len(SIMULATION_MODES))],
                   [SIMULATION_MODE_NAMES[mode] for mode in SIMULATION_MODES])
        plt.legend()
        plt.grid(True, axis='y')
        plt.tight_layout()
        plt.savefig(f'{PLOTS_DIR}/protocol_vs_error_mode_throughput.png')
        plt.close()
    except Exception as e:
        logger.error(f"Error creating comparison plot: {e}")

    return completion_times, retransmissions, throughputs


def run_error_rate_test():
    """Test impact of different error rates across protocols for each simulation mode"""

    logger.info("=== Running Error Rate Impact Test ===")

    # Test each simulation mode separately
    for mode in SIMULATION_MODES:
        logger.info(f"Testing simulation mode: {SIMULATION_MODE_NAMES[mode]}")

        # Structure to hold results for each protocol
        completion_times = {protocol: [] for protocol in CONGESTION_PROTOCOLS}

        for protocol in CONGESTION_PROTOCOLS:
            for error_rate in ERROR_RATES:
                cumulative_time = 0
                successful_trials = 0

                for trial in range(TRIALS):
                    logger.info(
                        f"Mode {SIMULATION_MODE_NAMES[mode]} - Protocol {PROTOCOL_NAMES[protocol]} - Error Rate {error_rate * 100}% - Trial {trial + 1}")

                    try:
                        _, client_time, _, _, cwnd_h, rtt_h, rto_h = run_single_transfer(mode, error_rate, protocol)

                        # Only count successful transfers
                        if client_time > 0:
                            # Save detailed plots for a specific error rate (e.g., 20%)
                            if abs(error_rate - 0.2) < 0.01 and trial == 0:
                                plot_dynamics_vs_time(cwnd_h, rtt_h, rto_h,
                                                      f"mode{mode}_protocol{protocol}_error{int(error_rate * 100)}")

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
                completion_times[protocol].append(avg_time)
                logger.info(f"Average completion time: {avg_time:.3f}s")

        # Generate the comparison plot for this simulation mode
        try:
            plt.figure(figsize=(12, 8))
            for protocol in CONGESTION_PROTOCOLS:
                plt.plot(
                    [er * 100 for er in ERROR_RATES],
                    completion_times[protocol],
                    marker='o',
                    label=f"{PROTOCOL_NAMES[protocol]}"
                )

            plt.title(f'Completion Time vs Loss/Error Rate ({SIMULATION_MODE_NAMES[mode]})')
            plt.xlabel('Loss/Error Rate (%)')
            plt.ylabel('Completion Time (seconds)')
            plt.grid(True)
            plt.legend()
            plt.savefig(
                f'{PLOTS_DIR}/completion_vs_errorrate_{SIMULATION_MODE_NAMES[mode].replace(" ", "_").lower()}.png')
            plt.close()
        except Exception as e:
            logger.error(f"Error creating error rate plot: {e}")

    logger.info("Error rate tests completed.")


def run_timeout_value_test():
    """Test impact of different timeout values across protocols for each simulation mode"""
    logger.info("=== Running Timeout Value Impact Test ===")

    # Test each simulation mode separately
    for mode in SIMULATION_MODES:
        logger.info(f"Testing timeout impact for mode: {SIMULATION_MODE_NAMES[mode]}")

        # Structure to hold results for each protocol
        completion_times = {protocol: [] for protocol in CONGESTION_PROTOCOLS}

        for protocol in CONGESTION_PROTOCOLS:
            for timeout in TIMEOUT_VALUES:
                cumulative_time = 0
                successful_trials = 0

                for trial in range(TRIALS):
                    logger.info(
                        f"Mode {SIMULATION_MODE_NAMES[mode]} - Protocol {PROTOCOL_NAMES[protocol]} - Timeout {timeout * 1000}ms - Trial {trial + 1}")

                    try:
                        _, client_time, _, _, cwnd_h, rtt_h, rto_h = run_single_transfer(
                            mode,
                            TEST_ERROR_RATE,  # Fixed error rate
                            protocol,
                            initial_timeout=timeout
                        )

                        if client_time > 0:
                            # Save detailed plots for a specific timeout value
                            if abs(timeout - 0.05) < 0.01 and trial == 0:
                                plot_dynamics_vs_time(
                                    cwnd_h, rtt_h, rto_h,
                                    f"mode{mode}_protocol{protocol}_timeout{int(timeout * 1000)}"
                                )

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
                completion_times[protocol].append(avg_time)
                logger.info(f"Average completion time for timeout {timeout * 1000}ms: {avg_time:.3f}s")

        # Generate the comparison plot for this simulation mode
        try:
            plt.figure(figsize=(12, 8))
            for protocol in CONGESTION_PROTOCOLS:
                plt.plot(
                    [t * 1000 for t in TIMEOUT_VALUES],  # Convert to ms for display
                    completion_times[protocol],
                    marker='o',
                    label=f"{PROTOCOL_NAMES[protocol]}"
                )

            plt.title(
                f'Completion Time vs Timeout Value ({SIMULATION_MODE_NAMES[mode]}, Error Rate: {TEST_ERROR_RATE * 100}%)')
            plt.xlabel('Timeout Value (ms)')
            plt.ylabel('Completion Time (seconds)')
            plt.grid(True)
            plt.legend()
            plt.savefig(
                f'{PLOTS_DIR}/completion_vs_timeout_{SIMULATION_MODE_NAMES[mode].replace(" ", "_").lower()}.png')
            plt.close()
        except Exception as e:
            logger.error(f"Error creating timeout plot: {e}")

    logger.info("Timeout value tests completed.")


def run_window_size_test():
    """Test impact of different window sizes across protocols for each simulation mode"""
    logger.info("=== Running Window Size Impact Test ===")

    # Test each simulation mode separately
    for mode in SIMULATION_MODES:
        logger.info(f"Testing window size impact for mode: {SIMULATION_MODE_NAMES[mode]}")

        # Structure to hold results for each protocol
        completion_times = {protocol: [] for protocol in CONGESTION_PROTOCOLS}

        for protocol in CONGESTION_PROTOCOLS:
            for window in WINDOW_SIZES:
                cumulative_time = 0
                successful_trials = 0

                for trial in range(TRIALS):
                    logger.info(
                        f"Mode {SIMULATION_MODE_NAMES[mode]} - Protocol {PROTOCOL_NAMES[protocol]} - Window Size {window} - Trial {trial + 1}")

                    try:
                        _, client_time, _, _, cwnd_h, rtt_h, rto_h = run_single_transfer(
                            mode,
                            TEST_ERROR_RATE,  # Fixed error rate
                            protocol,
                            initial_cwnd=window
                        )

                        if client_time > 0:
                            # Save detailed plots for a specific window size
                            if window == 10 and trial == 0:
                                plot_dynamics_vs_time(
                                    cwnd_h, rtt_h, rto_h,
                                    f"mode{mode}_protocol{protocol}_window{window}"
                                )

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
                completion_times[protocol].append(avg_time)
                logger.info(f"Average completion time for window size {window}: {avg_time:.3f}s")

        # Generate the comparison plot for this simulation mode
        try:
            plt.figure(figsize=(12, 8))
            for protocol in CONGESTION_PROTOCOLS:
                plt.plot(
                    WINDOW_SIZES,
                    completion_times[protocol],
                    marker='o',
                    label=f"{PROTOCOL_NAMES[protocol]}"
                )

            plt.title(
                f'Completion Time vs Window Size ({SIMULATION_MODE_NAMES[mode]}, Error Rate: {TEST_ERROR_RATE * 100}%)')
            plt.xlabel('Window Size (segments)')
            plt.ylabel('Completion Time (seconds)')
            plt.grid(True)
            plt.legend()
            plt.savefig(
                f'{PLOTS_DIR}/completion_vs_windowsize_{SIMULATION_MODE_NAMES[mode].replace(" ", "_").lower()}.png')
            plt.close()
        except Exception as e:
            logger.error(f"Error creating window size plot: {e}")

    logger.info("Window size tests completed.")


def compare_protocols_all_modes():
    """Compare all protocols across all simulation modes in a single plot matrix"""
    logger.info("=== Running Comprehensive Protocol Comparison ===")

    # Fixed parameters
    error_rate = TEST_ERROR_RATE
    initial_timeout = 0.05  # 50ms
    initial_cwnd = 1

    # Create a matrix to store results: [protocol][mode][metric]
    results = {}
    for protocol in CONGESTION_PROTOCOLS:
        results[protocol] = {}
        for mode in SIMULATION_MODES:
            results[protocol][mode] = {
                'time': 0,
                'retrans': 0,
                'throughput': 0
            }

    # Run tests for each combination
    for protocol in CONGESTION_PROTOCOLS:
        for mode in SIMULATION_MODES:
            cumulative_time = 0
            cumulative_retrans = 0
            cumulative_throughput = 0
            successful_trials = 0

            for trial in range(max(1, TRIALS)):  # At least one trial
                logger.info(
                    f"Comprehensive comparison - Protocol: {PROTOCOL_NAMES[protocol]}, Mode: {SIMULATION_MODE_NAMES[mode]}, Trial {trial + 1}")

                try:
                    _, client_time, retrans, throughput, cwnd_h, rtt_h, rto_h = run_single_transfer(
                        mode,
                        error_rate,
                        protocol,
                        initial_timeout=initial_timeout,
                        initial_cwnd=initial_cwnd
                    )

                    if client_time > 0:
                        # Save plots for the first trial
                        if trial == 0:
                            plot_dynamics_vs_time(
                                cwnd_h, rtt_h, rto_h,
                                f"comprehensive_protocol{protocol}_mode{mode}"
                            )

                        cumulative_time += client_time
                        cumulative_retrans += retrans
                        cumulative_throughput += throughput
                        successful_trials += 1
                except Exception as e:
                    logger.error(f"Error in comprehensive comparison trial: {e}")

                # Clean up
                plt.close('all')
                gc.collect()
                time.sleep(1)

            # Calculate averages
            if successful_trials > 0:
                results[protocol][mode]['time'] = cumulative_time / successful_trials
                results[protocol][mode]['retrans'] = cumulative_retrans / successful_trials
                results[protocol][mode]['throughput'] = cumulative_throughput / successful_trials

    # Create a comprehensive heatmap matrix for each metric
    try:
        metrics = ['time', 'retrans', 'throughput']
        metric_names = {
            'time': 'Completion Time (seconds)',
            'retrans': 'Retransmissions',
            'throughput': 'Throughput (bytes/second)'
        }

        for metric in metrics:
            # Create data matrix
            data = np.zeros((len(CONGESTION_PROTOCOLS), len(SIMULATION_MODES)))

            for i, protocol in enumerate(CONGESTION_PROTOCOLS):
                for j, mode in enumerate(SIMULATION_MODES):
                    data[i, j] = results[protocol][mode][metric]

            # Create heatmap
            plt.figure(figsize=(12, 8))
            plt.imshow(data, cmap='viridis')

            # Add colorbar
            cbar = plt.colorbar()
            cbar.set_label(metric_names[metric])

            # Add labels
            plt.xticks(range(len(SIMULATION_MODES)), [SIMULATION_MODE_NAMES[mode] for mode in SIMULATION_MODES])
            plt.yticks(range(len(CONGESTION_PROTOCOLS)),
                       [PROTOCOL_NAMES[protocol] for protocol in CONGESTION_PROTOCOLS])

            # Add values in cells
            for i in range(len(CONGESTION_PROTOCOLS)):
                for j in range(len(SIMULATION_MODES)):
                    text = f"{data[i, j]:.2f}" if metric == 'time' else f"{int(data[i, j])}"
                    plt.text(j, i, text, ha="center", va="center", color="w")

            plt.xlabel('Simulation Mode')
            plt.ylabel('Congestion Control Protocol')
            plt.title(f'Comparison of {metric_names[metric]} Across All Protocols and Modes')
            plt.tight_layout()
            plt.savefig(f'{PLOTS_DIR}/comprehensive_matrix_{metric}.png')
            plt.close()

    except Exception as e:
        logger.error(f"Error creating comprehensive comparison matrix: {e}")

    logger.info("Comprehensive protocol comparison completed.")


def main():
    logger.info("Starting TCP congestion control protocol testing harness")

    try:
        # Test 1: Compare protocols across different error simulation modes
        try:
            run_error_simulation_mode_test()
        except Exception as e:
            logger.error(f"Error simulation mode test failed: {e}")

        # Test 2: Test impact of different error rates for each mode
        try:
            run_error_rate_test()
        except Exception as e:
            logger.error(f"Error rate test failed: {e}")

        # Test 3: Test impact of different timeout values for each mode
        try:
            run_timeout_value_test()
        except Exception as e:
            logger.error(f"Timeout value test failed: {e}")

        # Test 4: Test impact of different window sizes for each mode
        try:
            run_window_size_test()
        except Exception as e:
            logger.error(f"Window size test failed: {e}")

        # Test 5: Comprehensive comparison of all protocols across all modes
        try:
            compare_protocols_all_modes()
        except Exception as e:
            logger.error(f"Comprehensive comparison failed: {e}")

    except Exception as e:
        logger.error(f"Critical error in main: {e}")
    finally:
        # Clean up resources
        plt.close('all')
        gc.collect()

    logger.info("All tests completed. Plots saved to 'plots' directory.")


if __name__ == "__main__":
    main()