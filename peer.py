import socket
import threading
import time
import hashlib
import random
import logging
from queue import Queue

class PeerNode:
    """
    Represents a peer node in a peer-to-peer network.
    """
    def __init__(self, my_ip_address, my_port, seeds_addresses, config_file="config.txt"):
        """
        Initializes the PeerNode with its IP address, port, and seed node addresses.
        
        Args:
            my_ip_address (str): The IP address of this peer.
            my_port (int): The port number this peer listens on.
            seeds_addresses (set): A set of seed node addresses.
            config_file (str): The name of the configuration file containing seed addresses.
        """
        self.my_ip_address = my_ip_address
        self.my_port = my_port
        self.seeds_addresses = set()
        self.peers_from_seed = set()
        self.connected_peers = []
        self.message_list = []
        self.connect_seed_addr = []
        self.sock = None  # Initialize socket
        self.job_queue = Queue()
        self.num_threads = 3  # Number of threads for job execution
        self.job_numbers = [1, 2, 3]  # Job numbers to be executed

        # Logging configuration
        logging.basicConfig(filename='peer_network.log', format='%(asctime)s - %(message)s')
        self.network_logger = logging.getLogger()
        self.network_logger.setLevel(logging.DEBUG)

        self.load_seed_addresses(config_file)
        self.register_with_k_seeds()

        # Initialize and start threads
        self.initialize_threads()

    def load_seed_addresses(self, config_file):
        """
        Loads seed node addresses from the config file.
        
        Args:
            config_file (str): The name of the configuration file.
        """
        try:
            with open(config_file, "r") as file:
                seeds_address_list = file.read()
            temp = seeds_address_list.split("\n")

            for addr in temp:
                if addr:
                    addr = addr.split(":")
                    addr = self.my_ip_address + ":" + str(addr[1])
                    self.seeds_addresses.add(addr)
        except Exception as e:
            print(f"Error loading seed addresses: {e}")

    def peer_to_peer_connection(self, conn, addr):
        """
        Handles peer-to-peer connections, receiving and processing messages.
        
        Args:
            conn (socket): The socket connection to the peer.
            addr (tuple): The address of the peer.
        """
        while True:
            try:
                message = conn.recv(1024).decode('utf-8')
                received_data = message

                if message:
                    message_parts = message.split(":")
                    message_type = message_parts[0]

                    if "New Connect Request From" in message_type:
                        self.new_connection(conn, addr, message_parts)
                    elif "Liveness Request" in message_type:
                        self.liveness_reply(conn, message_parts)
                    elif "GOSSIP" in message_parts[3][0:6]:
                        self.forward_gossip_message(received_data)
            except Exception as e:
                print("Exception occurred:", e)
                break

        conn.close()

    def new_connection(self, conn, addr, message_parts):
        """
        Accepts a new connection from a peer, if the connection limit is not reached.
        
        Args:
            conn (socket): The socket connection to the peer.
            addr (tuple): The address of the peer.
            message_parts (list): Parts of the received message.
        """
        if len(self.connected_peers) < 4:
            conn.send("New Connect Accepted".encode('utf-8'))
            peer_address = str(addr[0]) + ":" + str(message_parts[2])
            self.connected_peers.append(Peer(peer_address))
            self.network_logger.info(f"Peer {self.my_ip_address}:{self.my_port} connected to Peer {peer_address}")

    def liveness_reply(self, conn, message_parts):
        """
        Replies to a liveness request with the peer's address.
        
        Args:
            conn (socket): The socket connection to the peer.
            message_parts (list): Parts of the received liveness request message.
        """
        liveness_reply_msg = "Liveness Reply:" + ":".join(message_parts[1:4]) + ":" + str(self.my_ip_address)
        conn.send(liveness_reply_msg.encode('utf-8'))

    def start_connection(self):
        """
        Starts listening for incoming connections from other peers.
        """
        self.sock.listen(5)
        print("Peer is Listening")
        while True:
            conn, addr = self.sock.accept()
            self.sock.setblocking(1)
            thread = threading.Thread(target=self.peer_to_peer_connection, args=(conn, addr))
            thread.start()

    def start_peer_connection(self, complete_peer_list, selected_peer_nodes_index):
        """
        Attempts to connect to a list of peers based on the provided indices.
        
        Args:
            complete_peer_list (list): A list of all available peers.
            selected_peer_nodes_index (list): A list of indices representing the peers to connect to.
        """
        for i in selected_peer_nodes_index:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_addr = complete_peer_list[i].split(":")
                ADDRESS = (str(peer_addr[0]), int(peer_addr[1]))
                sock.connect(ADDRESS)
                peer_address = complete_peer_list[i]
                self.connected_peers.append(Peer(peer_address))
                message = "New Connect Request From:" + str(self.my_ip_address) + ":" + str(self.my_port)
                sock.send(message.encode('utf-8'))
                print(sock.recv(1024).decode('utf-8'))
                sock.close()
                self.network_logger.info(f"Peer {self.my_ip_address}:{self.my_port} connected to Peer {peer_address}")
            except Exception as e:
                print(f"Peer Connection Error: {e}")

    def limit_connection(self, complete_peer_list):
        """
        Limits the number of peer connections and starts connections with a subset of peers.
        
        Args:
            complete_peer_list (list): A list of all available peers.
        """
        if len(complete_peer_list) > 0:
            limit = min(random.randint(1, len(complete_peer_list)), 4)
            selected_peer_nodes_index = random.sample(range(len(complete_peer_list)), limit)
            self.start_peer_connection(complete_peer_list, selected_peer_nodes_index)

    def union_peer_lists(self, complete_peer_list):
        """
        Unions the received peer list with the current peer list.
        
        Args:
            complete_peer_list (str): A comma-separated string of peer addresses.
        
        Returns:
            list: A list of unique peer addresses.
        """
        complete_peer_list = complete_peer_list.split(",")
        complete_peer_list.pop()
        temp = complete_peer_list.pop()
        temp = temp.split(":")
        self.my_ip_address = temp[0]  # Update IP address
        for i in complete_peer_list:
            if i:
                self.peers_from_seed.add(i)
        complete_peer_list = list(self.peers_from_seed)
        return complete_peer_list

    def connect_seeds(self):
        """
        Connects to seed nodes to retrieve the initial list of peers.
        """
        for i in range(0, len(self.connect_seed_addr)):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                seed_addr = self.connect_seed_addr[i].split(":")
                ADDRESS = (str(seed_addr[0]), int(seed_addr[1]))
                sock.connect(ADDRESS)
                MY_ADDRESS = str(self.my_ip_address) + ":" + str(self.my_port)
                sock.send(MY_ADDRESS.encode('utf-8'))
                message = sock.recv(10240).decode('utf-8')
                complete_peer_list = self.union_peer_lists(message)
                for peer in complete_peer_list:
                    print(peer)
                    self.network_logger.info(f"Peer {self.my_ip_address}:{self.my_port} received peer list from Seed {seed_addr[0]}:{seed_addr[1]}")
                sock.close()
            except Exception as e:
                print(f"Seed Connection Error: {e}")
        self.limit_connection(complete_peer_list)

    def register_with_k_seeds(self):
        """
        Registers with a subset of seed nodes to retrieve peer lists.
        """
        seeds_addresses = list(self.seeds_addresses)
        n = len(seeds_addresses)
        seed_nodes_index = set(random.sample(range(0, n), n // 2 + 1))
        seed_nodes_index = list(seed_nodes_index)
        for i in seed_nodes_index:
            self.connect_seed_addr.append(seeds_addresses[i])
        self.connect_seeds()

    def report_dead(self, peer):
        """
        Reports a dead peer to the seed nodes.
        
        Args:
            peer (str): The address of the dead peer.
        """
        dead_message = "Dead Node:" + peer + ":" + str(time.time()) + ":" + str(self.my_ip_address)
        print(dead_message)
        self.network_logger.info(f"Peer {self.my_ip_address}:{self.my_port} detected dead node: {peer}")
        for seed in self.connect_seed_addr:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                seed_address = seed.split(":")
                ADDRESS = (str(seed_address[0]), int(seed_address[1]))
                sock.connect(ADDRESS)
                sock.send(dead_message.encode('utf-8'))
                sock.close()
                self.network_logger.info(f"Peer {self.my_ip_address}:{self.my_port} reported dead node {peer} to Seed {seed_address[0]}:{seed_address[1]}")
            except Exception as e:
                print("Seed Down ", seed)

    def liveness_test(self):
        """
        Tests the liveness of connected peers by sending liveness requests.
        """
        while True:
            liveness_request = "Liveness Request:" + str(time.time()) + ":" + str(self.my_ip_address)
            print(liveness_request)
            for peer in self.connected_peers:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    peer_addr = peer.address.split(":")
                    ADDRESS = (str(peer_addr[0]), int(peer_addr[1]))
                    sock.connect(ADDRESS)
                    sock.send(liveness_request.encode('utf-8'))
                    print(sock.recv(1024).decode('utf-8'))
                    sock.close()
                    peer.i = 0
                except Exception as e:
                    peer.i = peer.i + 1
                    if peer.i == 3:
                        self.report_dead(peer.address)
                        self.connected_peers.remove(peer)
            time.sleep(13)

    def forward_gossip_message(self, received_message):
        """
        Forwards a gossip message to connected peers, avoiding duplicates.
        
        Args:
            received_message (str): The gossip message received.
        """
        hash_value = hashlib.sha256(received_message.encode()).hexdigest()
        if hash_value in self.message_list:
            pass
        else:
            self.message_list.append(str(hash_value))
            print(received_message)
            self.network_logger.info(f"Peer {self.my_ip_address}:{self.my_port} received gossip message: {received_message}")
            for peer in self.connected_peers:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    peer_addr = peer.address.split(":")
                    ADDRESS = (str(peer_addr[0]), int(peer_addr[1]))
                    sock.connect(ADDRESS)
                    sock.send(received_message.encode('utf-8'))
                    sock.close()
                    self.network_logger.info(f"Peer {self.my_ip_address}:{self.my_port} forwarded gossip message to Peer {peer.address}")
                except Exception as e:
                    continue

    def gossip(self):
        """
        Sends gossip messages to connected peers.
        """
        for i in range(10):
            gossip_message = str(time.time()) + ":" + str(self.my_ip_address) + ":" + str(self.my_port) + ":" + "GOSSIP" + str(i + 1)
            hash_value = hashlib.sha256(gossip_message.encode()).hexdigest()
            self.message_list.append(str(hash_value))
            for peer in self.connected_peers:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    peer_addr = peer.address.split(":")
                    ADDRESS = (str(peer_addr[0]), int(peer_addr[1]))
                    sock.connect(ADDRESS)
                    sock.send(gossip_message.encode('utf-8'))
                    sock.close()
                    self.network_logger.info(f"Peer {self.my_ip_address}:{self.my_port} sent gossip message to Peer {peer.address}")
                except Exception as e:
                    print("Peer Down ", peer.address)
            time.sleep(5)

    def execute_job(self):
        """
        Executes jobs from the job queue.
        """
        while True:
            x = self.job_queue.get()
            if x == 1:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ADDRESS = (self.my_ip_address, self.my_port)
                self.sock.bind(ADDRESS)
                self.start_connection()
            elif x == 2:
                self.liveness_test()
            elif x == 3:
                self.gossip()
            self.job_queue.task_done()

    def initialize_threads(self):
        """
        Initializes and starts the threads for executing jobs.
        """
        for _ in range(self.num_threads):
            thread = threading.Thread(target=self.execute_job)
            thread.daemon = True
            thread.start()
        for i in self.job_numbers:
            self.job_queue.put(i)

    def run(self):
        """
        Starts the peer node operations.
        """
        self.job_queue.join()

class Peer:
    """
    Represents a peer in the network.
    """
    i = 0
    address = ""

    def __init__(self, addr):
        """
        Initializes a Peer object with its address.
        
        Args:
            addr (str): The address of the peer.
        """
        self.address = addr

if __name__ == "__main__":
    my_ip_address = "172.31.79.28" # Yatharth_ip_address
#   my_ip_address = "172.31.54.109" # Mayank_ip_address
    my_port = int(input("Enter your port: "))
    seeds_addresses = set()

    peer_node = PeerNode(my_ip_address, my_port, seeds_addresses)
    peer_node.run()
