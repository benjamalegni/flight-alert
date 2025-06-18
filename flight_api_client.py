# flight_api_client.py
# This script is designed to interact with the SerpApi Google Flights API
# to search for flights and retrieve information.

import os
import calendar
from datetime import datetime, timedelta
from serpapi import SerpApiClient, serp_api_client_exception
from dotenv import load_dotenv

load_dotenv()


def search_flights_api(origin_airport_code, destination_airport_code, search_date):
    """
    Searches for flights using the SerpApi Google Flights API.

    Args:
        origin_airport_code (str): The IATA code for the origin airport (e.g., "EZE").
        destination_airport_code (str): The IATA code for the destination airport (e.g., "BCN").
        search_date (str): The date of the flight in YYYY-MM-DD format (e.g., "2024-12-01").

    Returns:
        list: A list of flight dictionaries, or an empty list if an error occurs or no flights are found.
    """
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        print("Error: SERPAPI_KEY environment variable not found.")
        return []

    params = {
        "engine": "google_flights",
        "departure_id": origin_airport_code,
        "arrival_id": destination_airport_code,
        "outbound_date": search_date,
        "api_key": api_key,
        "currency": "USD",  # Optional: specify currency
        "hl": "en"          # Optional: specify language
    }

    print(f"Attempting to search flights using SerpApi with params: {params}")

    try:
        client = SerpApiClient(params)
        results = client.get_dict()

        if "error" in results:
            print(f"SerpApi Error: {results['error']}")
            return []

        processed_flights = []
        # SerpApi typically returns flight data in 'best_flights' or 'other_flights'
        flight_categories = ["best_flights", "other_flights"]

        for category in flight_categories:
            if category in results and results[category]:
                for flight_info in results[category]:
                    # Ensure 'flights' key exists and is a list
                    if "flights" in flight_info and isinstance(flight_info["flights"], list) and flight_info["flights"]:
                        first_leg = flight_info["flights"][0] # Assuming we are interested in the first leg for simplicity
                        flight_data = {
                            "airline": first_leg.get("airline"),
                            "flight_number": first_leg.get("flight_number"),
                            "price": flight_info.get("price"), # Price is usually at the top level of the flight offer
                            "departure_time": first_leg.get("departure_airport", {}).get("time")
                        }
                        processed_flights.append(flight_data)
                    elif not flight_info.get("flights") : # Handle cases where a flight offer might not have detailed flight legs (e.g. summarized offers)
                        flight_data = {
                             "airline": flight_info.get("airline_logo"), # Or some other identifier if airline name is not directly available
                             "flight_number": None, # Flight number might not be available in summarized offers
                             "price": flight_info.get("price"),
                             "departure_time": None # Departure time might not be available
                        }
                        # Add only if there's a price, to avoid adding empty entries if parsing fails for some offers
                        if flight_data["price"]:
                             processed_flights.append(flight_data)


        if not processed_flights and "message" in results: # Check for messages like "No flights found"
            print(f"SerpApi Message: {results['message']}")

        if processed_flights:
            print(f"Successfully processed {len(processed_flights)} flights from SerpApi.")
            return processed_flights
        else:
            print("No flight data found in SerpApi response or failed to parse.")
            return []

    except serp_api_client_exception as e:
        print(f"SerpApi Client Error: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

def find_cheapest_flights_in_month(origin_airport_code, destination_airport_code, year_month_str):
    """
    Finds the cheapest flight(s) in a given month by checking each day.

    Args:
        origin_airport_code (str): The IATA code for the origin airport.
        destination_airport_code (str): The IATA code for the destination airport.
        year_month_str (str): The month to search in "YYYY-MM" format.

    Returns:
        list: A list of the cheapest flight dictionaries found, including their date.
              Returns an empty list if no flights are found or an error occurs.
    """
    try:
        year, month = map(int, year_month_str.split('-'))
    except ValueError:
        print(f"Error: Invalid year_month_str format: {year_month_str}. Please use YYYY-MM.")
        return []

    num_days = calendar.monthrange(year, month)[1]
    all_flights_for_month = []

    print(f"\nSearching for all flights in {year_month_str} from {origin_airport_code} to {destination_airport_code}...")

    for day in range(1, num_days + 1):
        current_date_str = f"{year:04d}-{month:02d}-{day:02d}"
        print(f"Searching flights for {current_date_str}...")

        # Ensure SERPAPI_KEY is checked within the loop or rely on search_flights_api to handle it
        # For this implementation, we rely on search_flights_api's existing check.
        daily_flights = search_flights_api(origin_airport_code, destination_airport_code, current_date_str)

        if daily_flights: # search_flights_api returns [] on error or no flights
            for flight in daily_flights:
                # Ensure flight is a dictionary and has a 'price' before augmenting
                if isinstance(flight, dict) and 'price' in flight and flight['price'] is not None:
                    augmented_flight = flight.copy()
                    augmented_flight['date'] = current_date_str
                    all_flights_for_month.append(augmented_flight)
                # else:
                #     print(f"Debug: Skipping flight due to missing price or incorrect format: {flight}")


    if not all_flights_for_month:
        print(f"No flights found for {year_month_str} from {origin_airport_code} to {destination_airport_code}.")
        return []

    # Filter out flights without a valid price before finding the minimum
    valid_flights_with_price = [f for f in all_flights_for_month if isinstance(f.get('price'), (int, float))]

    if not valid_flights_with_price:
        print(f"No flights with valid prices found for {year_month_str} from {origin_airport_code} to {destination_airport_code}.")
        return []

    min_price = min(f['price'] for f in valid_flights_with_price)
    cheapest_flights = [f for f in valid_flights_with_price if f['price'] == min_price]

    print(f"\nFound {len(cheapest_flights)} cheapest flight(s) with price ${min_price:.2f} for {year_month_str} from {origin_airport_code} to {destination_airport_code}.")
    return cheapest_flights


if __name__ == "__main__":
    print("--- Starting Flight API Client (SerpApi) ---")
    # Example usage: Set your SERPAPI_KEY environment variable before running
    # export SERPAPI_KEY="your_actual_serpapi_key"

    serpapi_key_present = bool(os.getenv("SERPAPI_KEY"))
    if not serpapi_key_present:
        print("\nWARNING: SERPAPI_KEY environment variable is not set.")
        print("Please set it to your actual SerpApi key to test the API integration.")
        print("Example: export SERPAPI_KEY=\"your_key_here\"")
        print("\nProceeding with structural checks (no actual API calls will succeed without a key).")

    # Test case 1: Standard search (existing test)
    origin1 = "JFK"
    destination1 = "LAX"
    travel_date1 = "2024-07-15" # Using a past date for structure test if no key

    # Adjust travel_date if SERPAPI_KEY is present to a future date for better testing
    if serpapi_key_present:
        # Get tomorrow's date for a more likely successful search
        tomorrow = datetime.now() + timedelta(days=1)
        travel_date1 = tomorrow.strftime("%Y-%m-%d")


    print(f"\n--- Test Case 1: Daily Flight Search ---")
    print(f"Searching for flights: {origin1} to {destination1} on {travel_date1}")
    flights_daily = search_flights_api(origin1, destination1, travel_date1)

    if flights_daily:
        print(f"\nFound {len(flights_daily)} flights for {travel_date1}:")
        for i, flight in enumerate(flights_daily):
            print(f"  Flight #{i+1}:")
            print(f"    Airline: {flight.get('airline', 'N/A')}")
            print(f"    Flight Number: {flight.get('flight_number', 'N/A')}")
            price = flight.get('price', 'N/A')
            if isinstance(price, (int, float)):
                print(f"    Price: ${price:.2f}")
            else:
                print(f"    Price: {price}")
            print(f"    Departure Time: {flight.get('departure_time', 'N/A')}")
    else:
        print(f"\nNo flights found for {travel_date1} or an error occurred.")

    # Test case 2: Cheapest flight in a month
    origin2 = "EZE" # Buenos Aires
    destination2 = "BCN" # Barcelona
    # Use a future month for testing if API key is present, otherwise a fixed one for structure check
    search_month_str = "2025-12"
    if serpapi_key_present:
        # Example: Search for next month if key is present
        next_month_date = datetime.now().replace(day=1) + timedelta(days=32) # Approx next month
        search_month_str = next_month_date.strftime("%Y-%m")


    print(f"\n--- Test Case 2: Cheapest Flights in Month ---")
    print(f"Searching for cheapest flights from {origin2} to {destination2} in {search_month_str}")

    # Since find_cheapest_flights_in_month calls search_flights_api multiple times,
    # it will repeatedly print the SERPAPI_KEY error if not set.
    # This is expected behavior based on the current structure.
    cheapest_monthly_flights = find_cheapest_flights_in_month(origin2, destination2, search_month_str)

    if cheapest_monthly_flights:
        # The success message is printed within find_cheapest_flights_in_month
        print(f"\nDetails of cheapest flights found in {search_month_str}:")
        for i, flight in enumerate(cheapest_monthly_flights):
            print(f"  Cheapest Flight Option #{i+1}:")
            print(f"    Date: {flight.get('date', 'N/A')}")
            print(f"    Airline: {flight.get('airline', 'N/A')}")
            print(f"    Flight Number: {flight.get('flight_number', 'N/A')}")
            price = flight.get('price', 'N/A')
            if isinstance(price, (int, float)):
                print(f"    Price: ${price:.2f}")
            else:
                print(f"    Price: {price}")
            print(f"    Departure Time: {flight.get('departure_time', 'N/A')}")
    # find_cheapest_flights_in_month prints its own "no flights found" message
    elif not serpapi_key_present : # Add context if key is missing.
        print(f"\nNote: No flights found for {search_month_str}, as expected without SERPAPI_KEY or if no flights available.")


    print("\n--- Flight API Client (SerpApi) Finished ---")
