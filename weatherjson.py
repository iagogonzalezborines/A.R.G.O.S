import os
import requests

# Retrieve the API key from the environment variable
api_key = '88d7cd4138fd425eb86141809243108'

if not api_key:
    print("Error: WEATHER_API_KEY environment variable not set.")
    exit(1)

# Define the API endpoint
base_url = "http://api.weatherapi.com/v1"

# Example endpoint for current weather
endpoint = f"{base_url}/current.json"

# Define the location (can be changed as needed)
location = "Redondela, Pontevedra, Spain"

# Parameters for the API request
params = {
    'key': api_key,
    'q': location
}

try:
    # Make the API request
    response = requests.get(endpoint, params=params)
    response.raise_for_status()  # Check for HTTP errors
    weather_data = response.json()  # Parse JSON response

    # Display the weather information
    print(f"Weather information for {location}:")
    print(f"Location: {weather_data['location']['name']}, {weather_data['location']['region']}, {weather_data['location']['country']}")
    print(f"Temperature (Celsius): {weather_data['current']['temp_c']}")
    print(f"Condition: {weather_data['current']['condition']['text']}")
    print(f"Humidity: {weather_data['current']['humidity']}")
    print(f"Wind Speed (km/h): {weather_data['current']['wind_kph']}")

except requests.exceptions.RequestException as e:
    print(f"Error fetching weather data: {e}")
