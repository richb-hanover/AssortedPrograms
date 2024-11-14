# Code source: ChatGPT: https://chatgpt.com/c/66e4b86a-4344-8003-b2e4-70d745655fb4

import googlemaps

# Replace with your actual API key
API_KEY = 'AIzaSyAws1xyApa3jvcSCdtl6B201Ed1Uo--VRM'

# Initialize the Google Maps client
gmaps = googlemaps.Client(key=API_KEY)


def get_driving_times(destination_cities):
	origin = '03768'
	results = {}
	
	# Iterate over the list of destination cities
	for city in destination_cities:
		# Request the distance matrix for driving mode
		matrix = gmaps.distance_matrix(origins=origin, destinations=city,
									   mode="driving")
		
		# Extract driving time in hours
		if matrix['rows'][0]['elements'][0]['status'] == 'OK':
			driving_time_sec = matrix['rows'][0]['elements'][0]['duration'][
				'value']
			driving_time_hours = driving_time_sec / 3600  # Convert seconds to hours
			results[city] = driving_time_hours
		else:
			results[city] = 'N/A'
	
	return results


def read_cities_from_file(filename):
	"""Read city names from a file, one city per line."""
	with open(filename, 'r') as file:
		cities = [line.strip() for line in file if line.strip()]
	return cities


# Example usage
filename = 'cities.txt'  # Replace with the path to your city names file
cities = read_cities_from_file(filename)
driving_times = get_driving_times(cities)

for city, time in driving_times.items():
	print(f"Driving time to:\t {city}\t{time} \thours")
