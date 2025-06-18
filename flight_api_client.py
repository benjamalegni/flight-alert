# flight_api_client.py
# This script is designed to interact with a (currently fictional) flight data API
# to search for flights and retrieve information.
# It includes error handling and uses a mocked API response for development and testing.

import requests
import json

def search_flights_api(origin_airport_code, destination_airport_code, search_date):
    """
    Searches for flights using a fictional API for a given origin, destination, and date.
    Includes a mocked response for development as the API is not real.

    Args:
        origin_airport_code (str): The IATA code for the origin airport (e.g., "EZE").
        destination_airport_code (str): The IATA code for the destination airport (e.g., "BCN").
        search_date (str): The date of the flight in YYYY-MM-DD format (e.g., "2024-12-01").

    Returns:
        list: A list of flight dictionaries, or None if an error occurs.
    """
    base_api_url = "https://api.exampleflightdata.com/search" # Fictional API
    params = {
        'origin': origin_airport_code,
        'destination': destination_airport_code,
        'date': search_date
    }

    flights_data = None
    print(f"Attempting to search flights from API: {base_api_url} with params: {params}")

    try:
        # This request will likely fail as the URL is fictional.
        # response = requests.get(base_api_url, params=params, timeout=10)
        # response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        # flights_data_raw = response.json() # If the request was successful

        # Simulating a failure to trigger mock response
        raise requests.exceptions.ConnectionError("Simulated connection error to fictional API.")

    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        print("Using mocked API response for demonstration.")

        # Sample JSON response (as a Python dictionary/list structure)
        mock_response_data = [
            {"airline": "Fantasy Air", "price": 250.00, "departure_time": "10:00", "flight_number": "FA101"},
            {"airline": "Dream Flights", "price": 280.50, "departure_time": "12:30", "flight_number": "DF202"},
            {"airline": "Sky High", "price": 220.75, "departure_time": "15:00", "flight_number": "SH303"},
            {"airline": "Fantasy Air", "price": 260.00, "departure_time": "18:00", "flight_number": "FA105"}
        ]
        # In a real scenario where mock_response_data was a JSON string:
        # mock_response_json_str = """
        # [
        #   {"airline": "Fantasy Air", "price": 250.00, "departure_time": "10:00"},
        #   {"airline": "Dream Flights", "price": 280.50, "departure_time": "12:30"},
        #   {"airline": "Sky High", "price": 220.75, "departure_time": "15:00"}
        # ]
        # """
        # try:
        #     flights_data = json.loads(mock_response_json_str)
        # except json.JSONDecodeError as je:
        #     print(f"Error decoding mocked JSON response: {je}")
        #     return None

        # Since mock_response_data is already a Python list of dicts, we can use it directly
        flights_data = mock_response_data

    # This block would be for handling a real response's JSON parsing,
    # but here we've already assigned flights_data from the mock.
    # If flights_data_raw was populated from a real response:
    # try:
    #     flights_data = flights_data_raw # Assuming it's already a dictionary/list from response.json()
    # except json.JSONDecodeError as je:
    #     print(f"Error decoding API JSON response: {je}")
    #     return None
    # except Exception as ex: # Other potential errors with the response
    #     print(f"An unexpected error occurred processing the response: {ex}")
    #     return None

    if flights_data is not None:
        print("Successfully processed flight data (mocked).")
        return flights_data
    else:
        print("No flight data was processed.")
        return [] # Return empty list on failure to process/get data


if __name__ == "__main__":
    print("--- Starting Flight API Client ---")
    origin = "EZE"
    destination = "BCN"
    travel_date = "2024-12-01"

    print(f"\nSearching for flights: {origin} to {destination} on {travel_date}")
    flights = search_flights_api(origin, destination, travel_date)

    if flights:
        print(f"\n--- Found {len(flights)} flights (mocked data) ---")
        for i, flight in enumerate(flights):
            print(f"Flight #{i+1}:")
            print(f"  Airline: {flight.get('airline', 'N/A')}")
            print(f"  Flight Number: {flight.get('flight_number', 'N/A')}")
            print(f"  Price: ${flight.get('price', 'N/A'):.2f}")
            print(f"  Departure Time: {flight.get('departure_time', 'N/A')}")
    elif flights == []: # Explicitly check for empty list from handled error
        print("\nNo flights found or an error occurred, but it was handled (empty list returned).")
    else: # Should not happen if function returns [] on error, but as a fallback
        print("\nFailed to retrieve flight information (function returned None or other).")

    print("\n--- Flight API Client Finished ---")
