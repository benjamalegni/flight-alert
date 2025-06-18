# flight_scraper.py
# This script is designed to scrape flight data from Google Flights.
# It includes functions to install necessary libraries, fetch flight data for a given route and date,
# and will eventually include parsing logic to extract relevant information.

import subprocess
import re # Added for regex in parsing

# --- Library Installation ---
def install_libraries():
    """
    Installs the necessary Python libraries (requests and beautifulsoup4) using pip.
    """
    print("Checking and installing required libraries...")
    try:
        subprocess.check_call(['pip', 'install', 'requests', 'beautifulsoup4'])
        print("Libraries installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing libraries: {e}")
        print("Please ensure pip is installed and you have internet connectivity.")
    except Exception as ex:
        print(f"An unexpected error occurred during library installation: {ex}")

# Call install_libraries at the beginning of script execution
install_libraries()

# Now that libraries are supposedly installed, we can import them.
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"Failed to import required libraries after installation: {e}")
    print("Please check your Python environment and pip installation.")
    # Exit if essential libraries are missing, as the script cannot function.
    exit(1)


# --- Flight Data Fetching ---
def fetch_flight_data(origin_airport_code, destination_airport_code, date):
    """
    Fetches and parses the HTML content of a Google Flights page
    for a given origin, destination, and date using BeautifulSoup.

    Args:
        origin_airport_code (str): The IATA code for the origin airport (e.g., "EZE").
        destination_airport_code (str): The IATA code for the destination airport (e.g., "BCN").
        date (str): The date of the flight in YYYY-MM-DD format (e.g., "2024-12-01").

    Returns:
        BeautifulSoup: A BeautifulSoup object representing the parsed HTML, or None if an error occurs.
    """
    url = f"https://www.google.com/travel/flights?q=flights%20from%20{origin_airport_code}%20to%20{destination_airport_code}%20on%20{date}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
    }

    print(f"Fetching flight data from: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        print("Successfully fetched page content.")

        print("Parsing HTML content with BeautifulSoup...")
        # response.text should handle content decoding (e.g. gzip)
        soup = BeautifulSoup(response.text, "html.parser")
        print("HTML content parsed successfully.")
        return soup

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e} - Status code: {e.response.status_code}")
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 429:
                print("Error 429: Too Many Requests. Google may be rate-limiting.")
            elif e.response.status_code == 503:
                print("Error 503: Service Unavailable. Google Flights might be temporarily down or blocking requests.")
            # print(f"Response content for error: {response.text[:500]}") # Careful with this
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error occurred: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Timeout error occurred: {e}")
    except requests.exceptions.RequestException as e:
        print(f"An general error occurred during the request: {e}")
    except Exception as e:
        print(f"An error occurred during HTML parsing with BeautifulSoup: {e}")

    return None

# --- Flight Data Parsing ---
def parse_flight_data(soup):
    """
    Parses the BeautifulSoup object to extract flight information.
    This version uses highly speculative selectors.
    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the parsed HTML of the flight results page.
    Returns:
        list: A list of dictionaries, where each dictionary contains details of a flight.
              Returns an empty list if no flight data is found or if parsing fails.
    """
    if not soup:
        print("No soup object provided to parse_flight_data.")
        return []

    flights_data = []
    print("\n--- Starting Flight Data Parsing Logic ---")

    # HYPOTHETICAL selectors - these need to be found by inspecting actual Google Flights HTML.
    # Using very generic selectors as placeholders.
    # Option 1: Look for divs with jscontroller (common in Google apps)
    flight_containers = soup.find_all('div', attrs={'jscontroller': True})

    # Option 2: Fallback to divs with role="listitem" (ARIA pattern for lists)
    if not flight_containers:
        print("Primary selector (jscontroller) found 0 containers. Trying role='listitem'.")
        flight_containers = soup.find_all('div', role='listitem')

    # Option 3: Fallback to a hypothetical generic class (less likely to work without knowing the class)
    if not flight_containers:
        print("Secondary selector (role='listitem') found 0 containers. Trying class 'trip_card' (hypothetical).")
        flight_containers = soup.find_all('div', class_='trip_card') # Purely hypothetical

    print(f"Found {len(flight_containers)} potential flight container(s) using combined heuristics.")

    if not flight_containers:
        print("Could not find any elements matching the placeholder flight container selectors.")
        print("The HTML structure might be different than expected, or the page didn't load flight results.")
        # print("\nFirst 1000 chars of soup to debug:\n", str(soup)[:1000]) # Uncomment for debugging
        return []

    for i, container in enumerate(flight_containers):
        print(f"\nProcessing potential flight container #{i+1} of {len(flight_containers)}")
        flight_info = {'price': 'Not found', 'airline': 'Not found', 'details': 'Not found'}

        # Price Parsing Logic (Hypothetical)
        try:
            # Try a specific (but made up) class for price
            price_element = container.find('span', class_='price_value') # Example: <span class="price_value">$123</span>
            if not price_element:
                # Fallback: Find spans/divs with text matching currency patterns
                price_element = container.find(['span', 'div'], string=re.compile(r'[\$\€\£]\s*\d+([.,]\d+)?'))

            if price_element:
                flight_info['price'] = price_element.get_text(strip=True)
                print(f"  Price found: {flight_info['price']}")
            else:
                print("  Price element not found with current selectors/patterns.")
        except Exception as e:
            print(f"  Error parsing price: {e}")

        # Airline Parsing Logic (Hypothetical)
        try:
            # Try a specific (but made up) class for airline
            airline_element = container.find(['span','div'], class_='airline_name') # Example: <span class="airline_name">Airline X</span>
            if not airline_element:
                # Fallback: Look for img alt text that might contain airline names
                img_tag = container.find('img', alt=True)
                if img_tag and ('airline' in img_tag['alt'].lower() or 'logo' in img_tag['alt'].lower()):
                    airline_element_text = img_tag['alt']
                # Fallback: Look for spans/divs with text like "Airline", "Operated by"
                else:
                    airline_element = container.find(['span','div'], string=re.compile(r'(?i)\w+\s+(Airways|Airlines|Air|Lines|Flights|SA|LLC)|Operated by'))

            if airline_element: # If found by class or complex regex
                 flight_info['airline'] = airline_element.get_text(strip=True) if hasattr(airline_element, 'get_text') else str(airline_element)
                 print(f"  Airline found: {flight_info['airline']}")
            elif 'airline_element_text' in locals() and airline_element_text: # from img alt
                 flight_info['airline'] = airline_element_text.strip()
                 print(f"  Airline found (from img alt): {flight_info['airline']}")
            else:
                print("  Airline element not found with current selectors/patterns.")
        except Exception as e:
            print(f"  Error parsing airline: {e}")

        # Generic details from the container
        try:
            container_text = container.get_text(separator=' | ', strip=True)
            flight_info['details'] = container_text[:200] + "..." if len(container_text) > 200 else container_text
            if flight_info['price'] == 'Not found' and flight_info['airline'] == 'Not found':
                 print(f"  Container text snippet (since specific data not found): {flight_info['details'][:100]}...")
        except Exception as e:
            print(f"  Error extracting generic details: {e}")

        # Add to results if something specific was found, or if it's one of the few containers and nothing else was found
        if flight_info['price'] != 'Not found' or flight_info['airline'] != 'Not found':
            flights_data.append(flight_info)
            print(f"  Added flight to results: Price - {flight_info['price']}, Airline - {flight_info['airline']}")
        elif len(flights_data) < 5 and (flight_info['price'] == 'Not found' and flight_info['airline'] == 'Not found'): # Add some raw if nothing specific
            flights_data.append(flight_info) # Add with "Not found" for price/airline but with details
            print(f"  Added flight to results (only generic details found): {flight_info['details'][:100]}...")


    if not flights_data and flight_containers:
        print("\nFound potential flight containers, but could not extract specific price/airline information using current selectors.")
        print("This indicates that the selectors for price/airline are incorrect for the current HTML structure.")
        print("Returning raw text from first few containers as a fallback if any details were captured.")
        for i, container in enumerate(flight_containers[:min(3, len(flight_containers))]): # Limit to first 3 or less
             if not any(fd['details'] == (container.get_text(separator=' | ', strip=True)[:200] + "...") for fd in flights_data): # Avoid duplicates
                flights_data.append({
                    'price': 'Not found (final fallback)',
                    'airline': 'Not found (final fallback)',
                    'details': container.get_text(separator=' | ', strip=True)[:200] + "..."
                })
        if flights_data:
             print(f"Returning raw text from up to {len(flights_data)} containers as a fallback.")
    elif not flight_containers:
        print("No flight containers found at all.")


    print(f"\n--- Finished Flight Data Parsing. Found {len(flights_data)} entries. ---")
    return flights_data

# --- Main Execution ---
if __name__ == "__main__":
    print("\n--- Starting Flight Data Scrape and Parse ---")
    origin = "EZE"
    destination = "BCN"
    # Using a date far in the future to increase likelihood of results and avoid issues with past dates.
    flight_date = "2024-12-25"

    soup_object = fetch_flight_data(origin, destination, flight_date)

    if soup_object:
        print("\nSuccessfully fetched and created BeautifulSoup object.")

        # For debugging, you can save the soup to a file:
        with open("debug_soup.html", "w", encoding="utf-8") as f:
            f.write(str(soup_object))
        print("Saved soup to debug_soup.html for inspection.")

        flight_results = parse_flight_data(soup_object)

        if flight_results:
            print(f"\n--- Extracted Flight Data ({len(flight_results)} result(s)) ---")
            for i, flight in enumerate(flight_results):
                print(f"Flight #{i+1}:")
                print(f"  Price: {flight.get('price', 'N/A')}")
                print(f"  Airline: {flight.get('airline', 'N/A')}")
                # Only print details if price or airline is 'Not found', to avoid redundancy
                if flight.get('price', 'N/A') == 'Not found' or flight.get('airline', 'N/A') == 'Not found' or flight.get('price', '').startswith('Not found'):
                    print(f"  Details: {flight.get('details', 'N/A')}")
        else:
            print("\nNo flight data extracted by parse_flight_data.")
            print("This could be due to: \n1. No flights available for the given route/date. \n2. Page structure has changed significantly. \n3. CAPTCHA or consent wall blocking meaningful content. \n4. Incorrect or too generic selectors in `parse_flight_data`.")

    else:
        print(f"\nFailed to retrieve or parse flight data page for {origin} to {destination} on {flight_date}.")
        print("This could be due to network issues, HTTP errors (like 429 Too Many Requests or 503 Service Unavailable), or critical parsing errors in fetch_flight_data.")

    print("\n--- Script Finished ---")
