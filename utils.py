import threading

# Global thread lock to prevent asynchronous print statements
# from colliding and breaking the terminal UI output.
print_lock = threading.Lock()

def safe_print(text):
    """Prints text sequentially to the console in a thread-safe manner."""
    with print_lock:
        print(text)