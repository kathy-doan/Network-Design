"""
Benjamin Dearden
EECE 4830
Project Phase 1
Helper function
"""


def make_packet(file_name, server_name, server_port, client_socket):
    try:
        with open(file_name, "rb") as file_to_read:
            packet_size = 1024
            sequence_number = 0
            while True:
                packet = file_to_read.read(packet_size)
                if not packet:
                    break

                sequenced_packet = bytes(f"{sequence_number}|", 'utf-8') + packet

                client_socket.sendto(sequenced_packet, (server_name, server_port))
                sequence_number += 1

            client_socket.sendto("END".encode(), (server_name, server_port))
            while True:
                data, address = client_socket.recvfrom(1024)
                if data.decode() == "ACK":
                    break
    except Exception as e:
        print(f"Error while sending packets: {e}")
