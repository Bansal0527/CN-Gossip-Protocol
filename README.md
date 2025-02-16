# Peer-to-Peer Network Simulation

This project simulates a peer-to-peer (P2P) network using Python. The network consists of two types of nodes: **Seed** nodes and **Peer** nodes. Seed nodes act as central coordinators that maintain a list of active peers, while Peer nodes communicate with each other and the Seed nodes to exchange information, gossip messages, and perform liveness checks.

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [How It Works](#how-it-works)
4. [Setup and Execution](#setup-and-execution)
5. [Load Handling](#load-handling)
6. [Configuration](#configuration)
7. [Output Files](#output-files)
8. [Contributing](#contributing)
9. [License](#license)

---

## Overview

The project simulates a decentralized P2P network where:
- **Seed Nodes**: Maintain a list of active peers and distribute this list to new peers joining the network.
- **Peer Nodes**: Connect to Seed nodes to get the list of active peers, communicate with other peers, and perform gossip and liveness checks.

The system is designed to handle dynamic peer connections, detect dead peers, and limit the number of connections to manage load efficiently.

---

## Features

1. **Dynamic Peer Discovery**: Peers can join the network by connecting to Seed nodes and receiving an updated list of active peers.
2. **Gossip Protocol**: Peers exchange gossip messages to propagate information across the network.
3. **Liveness Checks**: Peers periodically check the liveness of other peers and report dead nodes to the Seed.
4. **Connection Limiting**: Peers limit the number of active connections to avoid overloading the network.
5. **Multi-threading**: Each peer runs multiple threads for listening, gossiping, and liveness testing.

---

## How It Works

### Seed Node
1. **Socket Creation**: The Seed node creates a socket, binds it to an IP and port, and listens for incoming connection requests.
2. **Peer Connection Handling**: When a peer connects, the Seed node creates a separate thread to handle the connection.
3. **Peer List Distribution**: The Seed node sends its list of active peers to the newly connected peer.
4. **Dead Peer Removal**: If the Seed node receives a "dead node" message, it removes the peer from its list.

### Peer Node
1. **Seed Connection**: The peer reads the Seed node's address from a configuration file and sends a connection request.
2. **Peer List Retrieval**: The peer receives the list of active peers from the Seed node and connects to a random subset of them.
3. **Multi-threading**: The peer creates three threads:
   - **Listening Thread**: Listens for incoming messages from other peers.
   - **Gossip Thread**: Generates and forwards gossip messages.
   - **Liveness Thread**: Periodically checks the liveness of connected peers.
4. **Dead Node Reporting**: If a peer detects a dead node, it sends a "dead node" message to the Seed node.

---

## Setup and Execution

### Prerequisites
- Python 3.x
- A text editor to modify configuration files.

### Steps to Run the Simulation

1. **Open the Project Folder**:
   - Navigate to the project directory containing `seed.py`, `peer.py`, and `config.txt`.

2. **Configure the System**:
   - Open `config.txt` and add the system's IP address and port number in the format `IP:PORT`.
   - Add the addresses of all Seed nodes manually in the same format.

3. **Run Seed Nodes**:
   - Open a terminal and navigate to the project directory.
   - Run the Seed node using the command:
     ```bash
     python3 seed.py
     ```
   - Based on the number of Seed entries in `config.txt`, run multiple instances of Seed nodes with different port numbers.

4. **Run Peer Nodes**:
   - Open a new terminal and navigate to the project directory.
   - Run the Peer node using the command:
     ```bash
     python3 peer.py
     ```
   - Provide a unique port number for each peer when prompted.
   - Repeat this step to create multiple peers.

---

## Load Handling

To manage the load on the network, each peer limits the number of active connections it maintains. This is achieved using the `limit_connection` function:

```python
def limit_connection(self, complete_peer_list):
    """
    Limits the number of peer connections and starts connections with a subset of peers.
    """
    if len(complete_peer_list) > 0:
        limit = min(random.randint(1, len(complete_peer_list)), 4)
        selected_peer_nodes_index = random.sample(range(len(complete_peer_list)), limit)
        self.start_peer_connection(complete_peer_list, selected_peer_nodes_index)
```

- **Connection Limit**: Each peer randomly selects a subset of peers to connect to, with a maximum of 4 connections.
- **Random Selection**: The selection of peers is randomized to ensure a balanced distribution of connections across the network.

---

## Configuration

The `config.txt` file contains the IP addresses and port numbers of the Seed nodes. Each line in the file should follow the format:
```
IP:PORT
```
Example:
```
192.168.1.1:5000
192.168.1.2:5001
```

---

## Output Files

The simulation generates output files that log the activities of Seed and Peer nodes. These files include:
- **Seed Logs**: Records peer connections, peer list updates, and dead node removals.
- **Peer Logs**: Records gossip messages, liveness checks, and connection statuses.

---

