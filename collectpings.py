import subprocess
import json
import time
from datetime import datetime
import platform
import os


def ping_host(host):
	try:
		if platform.system().lower() == 'windows':
			cmd = ['ping', '-n', '1', host]
			output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
											 text=True)
			if 'time=' in output:
				time_str = output.split('time=')[1].split('ms')[0].strip()
				return float(time_str)
		else:
			cmd = ['ping', '-c', '1', host]
			output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
											 text=True)
			if 'time=' in output:
				time_str = output.split('time=')[1].split(' ms')[0].strip()
				return float(time_str)
	except:
		pass
	return "0/0"


def load_existing_data(filename):
	try:
		with open(filename, 'r') as f:
			return json.load(f)
	except:
		return []


def save_data(data, filename):
	with open(filename, 'w') as f:
		f.write('[\n')
		for i, row in enumerate(data):
			f.write('  ' + json.dumps(row))
			if i < len(data) - 1:
				f.write(',\n')
			else:
				f.write('\n')
		f.write(']\n')


def main():
	host = 'gstatic.com'
	filename = 'ping.json'
	interval = 30
	
	data = load_existing_data(filename)
	print(f"Starting ping collection for {host}")
	print(f"Saving to {filename}")
	print(f"Press Ctrl+C to stop")
	
	try:
		current_row = []
		last_hour = datetime.now().hour
		current_row.append(
			datetime.now().strftime('%H:%M:%S'))  # Start time for this row
		
		while True:
			current_time = datetime.now()
			ping_time = ping_host(host)
			current_row.append(ping_time)
			
			timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
			print(f"{timestamp}: {ping_time}")
			
			# Check if hour has changed
			if current_time.hour != last_hour:
				if len(current_row) > 1:  # Save current row if it has data
					data.append(current_row)
					save_data(data, filename)
				current_row = []
				current_row.append(current_time.strftime('%H:%M:%S'))
				last_hour = current_time.hour
			
			time.sleep(interval)
	
	except KeyboardInterrupt:
		print("\nStopping ping collection")
		if len(current_row) > 1:  # Save partial row if it has data beyond timestamp
			data.append(current_row)
			save_data(data, filename)


if __name__ == '__main__':
	main()