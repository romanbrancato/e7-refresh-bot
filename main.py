import time

from client import Client
from detection import *


def main():
    client = Client("127.0.0.1:5557")
    start_time = time.time()

    # Run the command
    result = scan(client.capture_screen())

    # Record the end time
    end_time = time.time()

    # Calculate the elapsed time
    elapsed_time = end_time - start_time

    # Print the result and the elapsed time
    print(f"Scan result: {result}")
    print(f"Elapsed time: {elapsed_time} seconds")


if __name__ == '__main__':
    main()
