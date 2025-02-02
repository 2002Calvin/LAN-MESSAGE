import socket
import threading
import customtkinter as ctk
from tkinter import messagebox, simpledialog
from model.models import ChatMessage, Session  # Import the ChatMessage class and Session

# Server configuration
HOST = '127.0.0.1'
PORT = 3001

# CustomTkinter appearance settings
ctk.set_appearance_mode("dark")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Awesome Chat App")
        self.root.geometry("800x600")

        # Connect to the server
        self.username = simpledialog.askstring("Username", "Enter your username:", parent=root)
        if not self.username:
            messagebox.showerror("Error", "Username is required!")
            root.destroy()
            return

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((HOST, PORT))
            self.client_socket.send(self.username.encode('utf-8'))
        except:
            messagebox.showerror("Error", "Unable to connect to the server!")
            root.destroy()
            return

        self.session = Session()  # Initialize the database session

        # GUI Setup
        self.setup_ui()

        # Start a thread to receive messages
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        # Contact list on the left
        self.contact_frame = ctk.CTkFrame(self.main_frame, width=200)
        self.contact_frame.pack(side=ctk.LEFT, fill=ctk.Y, padx=(0, 10))

        self.contact_label = ctk.CTkLabel(self.contact_frame, text="Contacts", font=("Arial", 16, "bold"))
        self.contact_label.pack(pady=10)

        self.contact_listbox = ctk.CTkScrollableFrame(self.contact_frame)
        self.contact_listbox.pack(fill=ctk.BOTH, expand=True)

        # Chat window on the right
        self.chat_frame = ctk.CTkFrame(self.main_frame)
        self.chat_frame.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True)

        # Label to display the selected user
        self.chat_label = ctk.CTkLabel(self.chat_frame, text="Chat with All", font=("Arial", 14, "bold"))
        self.chat_label.pack(pady=10)

        self.chat_text = ctk.CTkScrollableFrame(self.chat_frame)
        self.chat_text.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        self.entry_frame = ctk.CTkFrame(self.chat_frame)
        self.entry_frame.pack(fill=ctk.X, padx=10, pady=(0, 10))

        self.entry = ctk.CTkEntry(self.entry_frame, placeholder_text="Type a message...")
        self.entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self.send_message)

        self.send_button = ctk.CTkButton(self.entry_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=ctk.RIGHT)

        # Default recipient
        self.selected_user = "All"

    def receive_messages(self):
        """Receive messages from the server."""
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                print(f"Received message: {message}")  # Debugging
                if message.startswith("USERLIST:"):
                    # Update the list of connected users
                    users = message.split(":")[1].split(",")
                    print(f"Updated user list: {users}")  # Debugging
                    self.update_contact_list(users)
                else:
                    # Display the message in the chat window
                    self.display_message(message, is_self=False)
            except Exception as e:
                print(f"Error receiving message: {e}")  # Debugging
                break

    def update_contact_list(self, users):
        """Update the contact list with connected users."""
        for widget in self.contact_listbox.winfo_children():
            widget.destroy()

        # Add "All" as the default contact
       # all_button = ctk.CTkButton(self.contact_listbox, text="All", command=lambda: self.select_user("All"))
       # all_button.pack(fill=ctk.X, pady=2)

        # Add other users (excluding the current user)
        for user in users:
            if user and user != self.username:
                user_button = ctk.CTkButton(self.contact_listbox, text=user, command=lambda u=user: self.select_user(u))
                user_button.pack(fill=ctk.X, pady=2)

    def select_user(self, user):
        """Select a user to chat with."""
        self.selected_user = user
        self.chat_label.configure(text=f"Chat with {user}")  # Update the chat label
        for widget in self.chat_text.winfo_children():
            widget.destroy()  # Clear the chat window

    def display_message(self, message, is_self=True):
        """Display a message in the chat window."""
        message_frame = ctk.CTkFrame(self.chat_text)
        message_frame.pack(fill=ctk.X, pady=2)

        # Check if the message is from the current user
        if is_self:
            message_label = ctk.CTkLabel(message_frame, text=message, fg_color="blue", corner_radius=10)
            message_label.pack(side=ctk.RIGHT, padx=5, pady=2)
        else:
            message_label = ctk.CTkLabel(message_frame, text=message, fg_color="gray", corner_radius=10)
            message_label.pack(side=ctk.LEFT, padx=5, pady=2)

    def send_message(self, event=None):
        """Send a message to the selected user."""
        message = self.entry.get()
        if message:
            # Display the message locally
            self.display_message(message, is_self=True)

            # Format: "recipient:message"
            formatted_message = f"{self.selected_user}:{message}"
            self.client_socket.send(formatted_message.encode('utf-8'))
            self.entry.delete(0, ctk.END)

    def user_exists(self, username):
        """Check if the username exists in the database."""
        return self.session.query(ChatMessage).filter_by(username=username).first() is not None

    def get_chat_with_user(self, username):
        """Retrieve all chat messages with the specified username."""
        messages = self.session.query(ChatMessage).filter_by(username=username).all()
        return messages

    def on_username_click(self, username):
        """Handle the event when a username is clicked."""
        if self.user_exists(username):
            chat_messages = self.get_chat_with_user(username)
            self.display_chat_history(chat_messages)
        else:
            print(f"User {username} does not exist.")

    def display_chat_history(self, messages):
        """Display the chat history for the selected user."""
        for message in messages:
            self.display_message(message.message, is_self=(message.username == self.username))

if __name__ == "__main__":
    root = ctk.CTk()
    app = ChatApp(root)
    root.mainloop()