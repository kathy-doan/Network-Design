#!/usr/bin/env python3
import threading
import time
import logging
import matplotlib

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
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
ERROR_RATES = [i / 100.0 for i in range(0, 65, 5)]  # 0%, 5%, ..., 80%
TRIALS = 4
FILENAME = "kitty.png"
# ----------------------

def run_single_transfer(mode: int, error_rate: float):
    server_time = None
    client_time = None
    retrans = None
    throughput = None

    def server_thr():
        nonlocal server_time
        server_time = run_server(mode, error_rate)

    def client_thr():
        nonlocal client_time, retrans, throughput
        client_time, retrans, throughput = send_file(mode, error_rate, file_name=FILENAME)

    t_s = threading.Thread(target=server_thr)
    t_s.start()
    time.sleep(0.5)  # give server a moment to bind()
    t_c = threading.Thread(target=client_thr)
    t_c.start()

    t_c.join()
    t_s.join()

    return server_time, client_time, retrans, throughput

def main():
    error_pcts = [int(er * 100) for er in ERROR_RATES]

    avg_server = {m: [] for m in SIMULATION_MODES}
    avg_client = {m: [] for m in SIMULATION_MODES}
    avg_retrans = {m: [] for m in SIMULATION_MODES}
    avg_tp = {m: [] for m in SIMULATION_MODES}

    for mode in SIMULATION_MODES:
        logger.info(f"=== MODE {mode} ===")
        for er in ERROR_RATES:
            stimes, ctimes, rlist, tplist = [], [], [], []
            for trial in range(1, TRIALS + 1):
                logger.debug(f"Mode {mode} – Error {er * 100:.0f}% – Run {trial}")
                s, c, r, t = run_single_transfer(mode, er)
                stimes.append(s)
                ctimes.append(c)
                rlist.append(r)
                tplist.append(t)
                time.sleep(1)

            avg_server[mode].append(sum(stimes) / len(stimes))
            avg_client[mode].append(sum(ctimes) / len(ctimes))
            avg_retrans[mode].append(sum(rlist) / len(rlist))
            avg_tp[mode].append(sum(tplist) / len(tplist))

    plots = [
        ("Average Client Completion Time vs Error Rate", avg_client, "Time (s)"),
        ("Average Retransmissions vs Error Rate", avg_retrans, "Retransmissions"),
        ("Average Throughput vs Error Rate", avg_tp, "Bytes/s"),
    ]

    for title, data_dict, ylabel in plots:
        plt.figure(figsize=(10, 6))
        for mode in SIMULATION_MODES:
            plt.plot(
                error_pcts,
                data_dict[mode],
                marker='o',
                label=f"Mode {mode}"
            )
        plt.title(title)
        plt.xlabel("Error Rate (%)")
        plt.ylabel(ylabel)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

    plt.show()

if __name__ == "__main__":
    main()
