import socket
import threading
import logging

class SeedNode:
    def __init__(self, ip, port):
        """
        Initializes the SeedNode.
        Args:
            ip (str): The IP address of the seed node.
            port (int): The port number the seed node listens on.
        """
        self.ip = ip
        self.port = port
        self.peers = []
        self.setup_logging()
        self.start_server()

    def setup_logging(self):
        """
        Configures logging for the seed node.
        """
        logging.basicConfig(filename='seed_network.log', format='%(asctime)s - %(message)s')
        self.network_logger = logging.getLogger()
        self.network_logger.setLevel(logging.DEBUG)

    def start_server(self):
        """
        Starts the server and listens for incoming connections.
        """
        with socket.socket() as self.network_socket:
            self.network_socket.bind((self.ip, self.port))
            self.network_socket.listen(5)
            print(f"Seed Node {self.ip}:{self.port} Listening .. . . .. ")
            self.network_logger.info(f"Seed Node {self.ip}:{self.port} started listening")

            while True:
                connection, address = self.network_socket.accept()
                self.network_socket.setblocking(1)
                communication_thread = threading.Thread(target=self.manage_connection, args=(connection, address))
                communication_thread.start()

    def manage_connection(self, connection, address):
        """
        Manages a connection with a peer.
        Args:
            connection (socket): The socket connection to the peer.
            address (tuple): The address of the peer.
        """
        while True:
            try:
                data = connection.recv(1024).decode('utf-8')
                if data:
                    if "Disconnected Node" in data[:15]:
                        print(data)
                        self.network_logger.info(data)
                        data = data.split(":")
                        disconnected_node = str(data[1]) + ":" + str(data[2])
                        if disconnected_node in self.peers:
                            self.peers.remove(disconnected_node)
                            self.network_logger.info(f"Seed Node {self.ip}:{self.port} - Disconnected Peer Node {disconnected_node}")
                    else:
                        data = data.split(":")
                        peer_address = str(address[0]) + ":" + str(data[1])
                        self.peers.append(peer_address)
                        message = f"Seed Node {self.ip}:{self.port} - Connected to Peer Node {peer_address}"
                        print(message)
                        self.network_logger.info(message)
                        peer_list_str = ",".join(self.peers) + ","
                        connection.send(peer_list_str.encode('utf-8'))
            except Exception as e:
                print("Error occurred:", e)
                break
        connection.close()

if __name__ == "__main__":
    my_ip = "172.31.79.28" # Yatharth_ip_address
#   my_ip_address = "172.31.54.109" # Mayank_ip_address
    port = int(input("Enter port: "))
    seed_node = SeedNode(my_ip, port)
