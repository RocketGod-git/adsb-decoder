# __________                  __             __     ________             .___ 
# \______   \  ____    ____  |  | __  ____ _/  |_  /  _____/   ____    __| _/ 
#  |       _/ /  _ \ _/ ___\ |  |/ /_/ __ \\   __\/   \  ___  /  _ \  / __ |  
#  |    |   \(  <_> )\  \___ |    < \  ___/ |  |  \    \_\  \(  <_> )/ /_/ |  
#  |____|_  / \____/  \___  >|__|_ \ \___  >|__|   \______  / \____/ \____ |  
#         \/              \/      \/     \/               \/              \/  
#
# ADS-B decoder by RocketGod
# Edit config.json before running

import subprocess
import sys

REQUIRED_PACKAGES = [
    'requests',
    'pyModeS',
    'colorama'
]

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_and_install_packages():
    missing_packages = []
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package)
        except ImportError:
            print(f"{package} not installed. Attempting to auto-install...")
            try:
                install_package(package)
                __import__(package)
                print(f"{package} installed successfully.")
            except subprocess.CalledProcessError:
                print(f"Failed to install {package}. Please install it manually.")

                missing_packages.append(package)
    
    if missing_packages:
        packages_str = " ".join(missing_packages)
        print(f"To install missing packages, run: \n\n{sys.executable} -m pip install {packages_str}\n")

# Ensure all required packages are installed
check_and_install_packages()

# Then continue with the rest of your script
import time
import requests
import pyModeS as pms
import json
from datetime import timedelta
import datetime
from requests.exceptions import HTTPError
from colorama import Fore, Style
from extrapack import decode_message


# Load config from config.json
with open('config.json', 'r') as file:
    config = json.load(file)

WEBHOOK_URL = config["WEBHOOK_URL"]
FILENAME = config["FILENAME"]

POSITION_MESSAGE_TIMEOUT = timedelta(minutes=2)
MESSAGE_RATE_LIMIT = timedelta(seconds=10)
DISCORD_RATE_LIMIT_PAUSE = 60  # Pause duration in seconds when Discord rate limit is reached

def display_header():
    header = """
 ________                  __             __     ________             .___ 
 \______   \  ____    ____  |  | __  ____ _/  |_  /  _____/   ____    __| _/ 
  |       _/ /  _ \ _/ ___\ |  |/ /_/ __ \\\\   __\/   \  ___  /  _ \  / __ |  
  |    |   \(  <_> )\  \___ |    < \  ___/ |  |  \    \_\  \(  <_> )/ /_/ |  
  |____|_  / \____/  \___  >|__|_ \ \___  >|__|   \______  / \____/ \____ |  
         \/              \/      \/     \/               \/              \/  
    """
    print(header)
    print("ADS-B decoder by RocketGod")
    print("Edit config.json before running")
    print("Listening on 1090 MHz for messages to decode...\n")

class AircraftState:
    def __init__(self):
        self.callsign = None
        self.altitude = 'N/A'
        self.velocity = 'N/A'
        self.heading = 'N/A'
        self.lat = None
        self.lon = None
        self.last_position_update = None
        self.last_even_message = None
        self.last_even_message_t = None
        self.last_odd_message = None
        self.last_odd_message_t = None
        self.last_message_time = None

aircraft_states = {}

def is_valid_webhook_url(url):
    if not url:
        return False
    # Add any other validations if needed
    return True

def process_line(line):
    parts = line.split(',')
    
    # Check that line contains at least three comma-separated fields and a timestamp
    if len(parts) < 3 or not parts[0].strip():
        return

    try:
        timestamp = datetime.datetime.strptime(parts[0], "%a %b %d %Y")  # adjust according to your timestamp format
        unix_timestamp = time.mktime(timestamp.timetuple())
        message = parts[2]
    except IndexError:
        return

    # If message is empty or not a hexadecimal string, or not and ADS-B message return
    if not message or not all(c in '0123456789abcdefABCDEF' for c in message) or pms.df(message) != 17:
        return

    icao = pms.adsb.icao(message)
    tc = pms.adsb.typecode(message)

    # Get aircraft state, create new if not exists
    if icao not in aircraft_states:
        aircraft_states[icao] = AircraftState()

    state = aircraft_states[icao]

    # Decode altitude, velocity, heading, and callsign if possible
    if 5 <= tc <= 8 or 20 <= tc <= 22 or 9 <= tc <= 18:
        try:
            state.altitude = pms.adsb.altitude(message)
        except RuntimeError:
            pass
    if tc == 19:
        state.velocity, state.heading = pms.adsb.speed_heading(message)
    if 1 <= tc <= 4:
        state.callsign = pms.adsb.callsign(message)
    if 9 <= tc <= 18:
        if pms.adsb.oe_flag(message):
            state.last_odd_message = message
            state.last_odd_message_t = unix_timestamp
        else:
            state.last_even_message = message
            state.last_even_message_t = unix_timestamp

        if state.last_odd_message and state.last_even_message:
            state.lat, state.lon = pms.adsb.position(state.last_even_message, state.last_odd_message, state.last_even_message_t, state.last_odd_message_t)
            state.last_position_update = datetime.datetime.now()

    # If position is too old, set to N/A
    if state.last_position_update and datetime.datetime.now() - state.last_position_update > POSITION_MESSAGE_TIMEOUT:
        state.lat = 'N/A'
        state.lon = 'N/A'

    # If callsign or position is not decoded, or if rate limit not passed, don't send the message
    if state.callsign is None or state.lat is None or state.lon is None or (state.last_message_time and datetime.datetime.now() - state.last_message_time < MESSAGE_RATE_LIMIT):
        return

    decoded_data = {
        'ICAO': icao,
        'TypeCode': tc,
        'Altitude': state.altitude,
        'Velocity': state.velocity,
        'Heading': state.heading,
        'Callsign': state.callsign,
        'Latitude': state.lat,
        'Longitude': state.lon,
    }

    # Decoding the message and merging with the existing data
    decoded_data_extended = decode_message(message)
    decoded_data.update(decoded_data_extended)

    # Pretty print output
    print(Fore.YELLOW + 'ICAO: ' + decoded_data['ICAO'], end=' ')
    print(Fore.GREEN + 'TypeCode: ' + str(decoded_data['TypeCode']), end=' ')
    print(Fore.CYAN + 'Altitude: ' + str(decoded_data['Altitude']), end=' ')
    print(Fore.BLUE + 'Velocity: ' + str(decoded_data['Velocity']), end=' ')
    print(Fore.MAGENTA + 'Heading: ' + str(decoded_data['Heading']), end=' ')
    print(Fore.RED + 'Callsign: ' + decoded_data['Callsign'], end=' ')
    print(Fore.GREEN + 'Latitude: ' + str(decoded_data['Latitude']), end=' ')
    print(Fore.CYAN + 'Longitude: ' + str(decoded_data['Longitude']))
    print(Style.RESET_ALL)

    send_message_to_discord(decoded_data)

    # Update last message time
    state.last_message_time = datetime.datetime.now()

def send_message_to_discord(decoded_data):
    if not is_valid_webhook_url(WEBHOOK_URL):
        print(Fore.RED + "Webhook URL is blank or invalid. Displaying output in terminal only.")
        print(Style.RESET_ALL)
        return
    
    data = {
        'content': '',
        'embeds': [{
            'title': 'New Aircraft Detected',
            'description': '\n'.join(f'{k}: {v}' for k, v in decoded_data.items())
        }]
    }
    while True:
        try:
            response = requests.post(WEBHOOK_URL, json=data)
            response.raise_for_status()
            break
        except HTTPError as err:
            if response.status_code == 429:  # Too Many Requests
                retry_after = response.json().get("retry_after", DISCORD_RATE_LIMIT_PAUSE)
                print(Fore.RED + f"Rate limit reached, pausing for {retry_after} seconds...")
                print(Style.RESET_ALL)
                time.sleep(retry_after)
            else:
                print(Fore.RED + f"HTTP error occurred: {err}")
                print(Style.RESET_ALL)
                break

def tail_file_and_process():
    while True:
        try:
            with open(FILENAME, 'r') as f:
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    process_line(line.strip())
        except Exception as e:
            print(f'Error occurred: {str(e)}, restarting...')
            time.sleep(1)

if __name__ == '__main__':
    display_header()
    try:
        tail_file_and_process()
    except KeyboardInterrupt:
        print('Interrupted by user, stopping.')