"""
Benjamin Dearden
EECE 4830
Project Phase 1
Helper function
"""
def make_packet(file_name, server_name, server_port, client_socket):
    try:
        with open(file_name, "rb") as bmp_file:
            packet_size = 1024
            while True:
                packet = bmp_file.read(packet_size)
                if not packet:
                    break
                client_socket.sendto(packet, (server_name, server_port))

            client_socket.sendto("END".encode(), (server_name, server_port))
    except Exception as e:
        print(f"Error while sending packets: {e}")
