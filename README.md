# ADS-B Aircraft Tracking with Discord Notifications

This project provides a script to track aircraft using Automatic Dependent Surveillance-Broadcast (ADS-B) data, and sends notifications to a Discord server via a webhook when new aircraft are detected.

## Prerequisites

- Python 3.7 or above
- Access to a source of ADS-B data, such as an SDR receiver like HackRF, RTL-SDR, SDRangel, or a log file with ADS-B messages.

## Dependencies

This project relies on a few Python libraries:
- `requests` for sending HTTP requests to the Discord webhook
- `pyModeS` for decoding ADS-B messages
- `colorama` for colored console output

To install these dependencies, run:

```bash
pip install requests pyModeS colorama
```

## Usage

1. Clone this repository or download the script `adsb-streamer.py`.

2. Update the `WEBHOOK_URL` variable in the script with your Discord webhook URL.

3. Update the `FILENAME` variable in the script with the path to your ADS-B data file.

The ADS-B data file should have lines in the following format:

```
Sun Jul 16 2023,11:31:40,5da9636cfa39ce25854eff84feda,13.2818
```

This includes a timestamp, the ADS-B message, and a signal strength value, separated by commas. This script currently uses only the timestamp and ADS-B message.

4. Run the script:

```bash
python adsb-streamer.py
```

The script will continuously read from the ADS-B data file, decode any aircraft information it can from the ADS-B messages, stream it in the terminal window, and send a notification to the specified Discord webhook whenever a new aircraft is detected.

## Notes

This script is designed to be robust and to handle various errors gracefully. If an error occurs during the reading or processing of lines from the file, the script will log the error, pause for 1 second, and then continue reading and processing lines. The script can be stopped by sending a `KeyboardInterrupt` (e.g., by pressing `Ctrl+C`).

## Using SDRangel to Generate ADS-B Data

SDRangel is a popular software-defined radio (SDR) receiver that can be used to receive ADS-B messages from aircraft. If you have an SDR device and want to use SDRangel to generate ADS-B data for this script, follow the instructions in the [SDRangel GitHub repository](https://github.com/f4exb/sdrangel) to install and configure SDRangel for ADS-B reception.

Once SDRangel is set up and receiving ADS-B messages, you can configure it to write the messages to a file in the required format. Then, you can point this script to that file to begin tracking aircraft and sending Discord notifications.

Please note that the quality and quantity of ADS-B data you can receive with SDRangel will depend on your location, the quality of your SDR device and antenna, and other factors.

Also, keep in mind that you can use any other source of ADS-B data, as long as the data is provided in the required format.

![RocketGod](https://github.com/RocketGod-git/adsb-decoder/assets/57732082/90f9eafd-e04d-4d2a-bc6f-5571f3f76022)
