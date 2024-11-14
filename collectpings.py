import subprocess
import json
import time
from datetime import datetime
import platform
import os


def ping_host(host):
	"""
	Ping the host and return the response time or '0/0' if failed.
	Handles different ping command formats for Windows vs Unix-like systems.
	"""
	try:
		if platform.system().lower() == 'windows':
			# Windows ping command
			cmd = ['ping', '-n', '1', host]
			output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
											 text=True)
			if 'time=' in output:
				# Extract time in ms
				time_str = output.split('time=')[1].split('ms')[0].strip()
				return float(time_str)
		else:
			# Unix-like ping command
			cmd = ['ping', '-c', '1', host]
			output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
											 text=True)
			if 'time=' in output:
				# Extract time in ms
				time_str = output.split('time=')[1].split(' ms')[0].strip()
				return float(time_str)
	except:
		pass
	
	return "0/0"


def load_existing_data(filename):
	"""Load existing ping data from file if it exists."""
	try:
		with open(filename, 'r') as f:
			return json.load(f)
	except:
		return []


def save_data(data, filename):
	"""Save ping data to file."""
	with open(filename, 'w') as f:
		json.dump(data, f, indent=2)


def main():
	host = 'gstatic.com'
	filename = 'ping.json'
	pings_per_row = 12  # Number of pings to collect per row/time period
	interval = 30  # Seconds between pings
	
	# Load existing data
	data = load_existing_data(filename)
	
	print(f"Starting ping collection for {host}")
	print(f"Saving to {filename}")
	print(f"Press Ctrl+C to stop")
	
	try:
		current_row = []
		while True:
			# Get ping time
			ping_time = ping_host(host)
			current_row.append(ping_time)
			
			# Print status
			timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			print(f"{timestamp}: {ping_time}")
			
			# If we've collected enough pings for a row, add it to data
			if len(current_row) >= pings_per_row:
				data.append(current_row)
				save_data(data, filename)
				current_row = []
			
			# Wait for next interval
			time.sleep(interval)
	
	except KeyboardInterrupt:
		print("\nStopping ping collection")
		# Save any remaining data
		if current_row:
			data.append(current_row)
			save_data(data, filename)


if __name__ == '__main__':
	main()