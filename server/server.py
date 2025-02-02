import socket
import threading

# Server configuration
HOST = '127.0.0.1'  # Localhost
PORT = 3001         # Port to listen on

# Store connected clients and their usernames
clients = {}
lock = threading.Lock()

def broadcast_userlist():
    """Send the updated list of connected users to all clients."""
    with lock:
        userlist = "USERLIST:All," + ",".join(clients.values())  # Add "All" to the user list
        for client_socket in clients:
            try:
                client_socket.send(userlist.encode('utf-8'))
            except:
                # Remove disconnected clients
                del clients[client_socket]

def send_message_to_client(message, recipient):
    """Send a message to a specific client."""
    with lock:
        for client_socket, username in clients.items():
            if username == recipient:
                try:
                    client_socket.send(message.encode('utf-8'))
                except:
                    del clients[client_socket]
                break

def broadcast(message, sender_socket=None):
    """Send a message to all connected clients except the sender."""
    with lock:
        for client_socket in clients:
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode('utf-8'))
                except:
                    # Remove disconnected clients
                    del clients[client_socket]

def handle_client(client_socket):
    """Handle communication with a connected client."""
    try:
        # Receive the username from the client
        username = client_socket.recv(1024).decode('utf-8')
        with lock:
            clients[client_socket] = username
        print(f"{username} has joined the chat.")
       # broadcast(f"{username} has joined the chat!", client_socket)
        broadcast_userlist()  # Send updated user list to all clients

        while True:
            # Receive messages from the client
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            # Parse the message (format: "recipient:message")
            if ":" in message:
                recipient, content = message.split(":", 1)
                if recipient == "All":
                    broadcast(f"{content}", client_socket)
                else:
                    send_message_to_client(f"{content}", recipient)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Remove the client when they disconnect
        with lock:
            if client_socket in clients:
                username = clients[client_socket]
                del clients[client_socket]
              #  print(f"{username} has left the chat.")
              #  broadcast(f"{username} has left the chat.", client_socket)
                broadcast_userlist()  # Send updated user list to all clients
        client_socket.close()

def start_server():
    """Start the chat server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server started on {HOST}:{PORT}")

    while True:
        client_socket, client_address = server.accept()
        print(f"New connection from {client_address}")
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_server()