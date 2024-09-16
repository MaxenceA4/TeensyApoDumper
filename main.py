import serial
import serial.tools.list_ports
import time
import os

# Configuration
BAUD_RATE = 921600  # Must match the monitor_speed in platformio.ini
OUTPUT_CSV = 'combined_output.csv'


def list_serial_ports():
    """ Lists all available serial ports. """
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


def select_serial_port():
    """ Prompts the user to select a serial port from the available list. """
    ports = list_serial_ports()
    if not ports:
        print("No serial ports found. Please connect your device.")
        return None

    print("Available serial ports:")
    for i, port in enumerate(ports):
        print(f"{i}: {port}")

    while True:
        try:
            choice = int(input(f"Select the serial port (0-{len(ports) - 1}): "))
            if 0 <= choice < len(ports):
                return ports[choice]
            else:
                print(f"Invalid selection. Choose a number between 0 and {len(ports) - 1}.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def read_from_serial(ser):
    """ Reads data from serial until it detects a newline. """
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    return line


def write_to_csv(file_name, data, output_csv):
    """ Appends data from a single file into the output CSV. """
    with open(output_csv, 'a') as f:
        # Write a header to indicate the source file
        f.write(f"# Data from {file_name}\n")
        f.write(data)
        f.write("\n")


def main():
    # Remove existing output CSV file if it exists
    if os.path.exists(OUTPUT_CSV):
        os.remove(OUTPUT_CSV)

    # Prompt the user to select a serial port
    selected_port = select_serial_port()
    if not selected_port:
        print("No serial port selected. Exiting...")
        return

    ser = None  # Initialize ser variable

    try:
        # Attempt to open the selected serial port
        ser = serial.Serial(selected_port, BAUD_RATE, timeout=2)
        time.sleep(2)  # Give time for the serial port to initialize

        print(f"Listening for data on {selected_port}...")

        # Request the Teensy to enter USB mode
        ser.write(b'U\n')
        time.sleep(1)  # Give some time for the Teensy to process the command

        while True:
            # Read file name or status from Teensy
            line = read_from_serial(ser)

            if "Iam done" in line:
                print("Data transfer completed.")
                break
            elif line.startswith("#"):
                # Ignore comment lines
                continue
            elif line:
                print(f"Receiving data from: {line}")

                # Start capturing file data
                file_data = []
                while True:
                    chunk = read_from_serial(ser)

                    if not chunk:  # End of file transmission
                        break

                    file_data.append(chunk)

                # Combine file data into a single string
                combined_data = "\n".join(file_data)
                write_to_csv(line, combined_data, OUTPUT_CSV)
                print(f"Saved data from {line} to {OUTPUT_CSV}")

        # After data retrieval, reboot the Teensy
        print("Sending reboot command to the Teensy...")
        ser.write(b'R\n')

    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
    finally:
        # Only attempt to close the serial port if it was successfully opened
        if ser and ser.is_open:
            ser.close()


if __name__ == "__main__":
    main()
