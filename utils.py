import threading
import datetime

# Lock to prevent console text from overlapping when multiple nodes receive packets simultaneously
print_lock = threading.Lock()

# Define the output file name
LOG_FILE = "simulation_log.txt"

# Initialize/clear the log file when the script starts
with open(LOG_FILE, "w") as f:
    f.write("=========================================\n")
    f.write(f" JUNGLE MESH SIMULATION LOG\n")
    f.write(f" Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=========================================\n")

def safe_print(*args, **kwargs):
    """Prints to the terminal AND writes to the log file safely. Used for summaries."""
    message = " ".join(str(arg) for arg in args)
    
    with print_lock:
        print(message, **kwargs)
        with open(LOG_FILE, "a") as f:
            f.write(message + "\n")

def log_only(*args, **kwargs):
    """Writes ONLY to the log file, keeping the terminal clean. Used for packet details."""
    message = " ".join(str(arg) for arg in args)
    
    with print_lock:
        with open(LOG_FILE, "a") as f:
            f.write(message + "\n")