# telegram_bot.py
# This script implements a Telegram bot for flight alerts and search.
# It uses the python-telegram-bot library and interacts with flight_api_client.py.

import subprocess
# --- Global Constants ---
PRICE_THRESHOLD = 300.00  # USD
import os
import logging
import re # For input validation

# --- Library Installation ---
def install_telegram_bot_library():
    """
    Installs the python-telegram-bot library using pip.
    """
    print("Checking and installing python-telegram-bot library...")
    try:
        subprocess.check_call(['pip', 'install', 'python-telegram-bot'])
        print("python-telegram-bot installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing python-telegram-bot: {e}")
        print("Please ensure pip is installed and you have internet connectivity.")
        # Depending on the environment, you might want to exit here.
        # For now, we'll let it continue, but the bot will fail if the library isn't there.
    except Exception as ex:
        print(f"An unexpected error occurred during library installation: {ex}")

# Call install_telegram_bot_library at the beginning of script execution
install_telegram_bot_library()

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    # Assuming flight_api_client.py is in the same directory
    from flight_api_client import search_flights_api, find_cheapest_flights_in_month
except ImportError:
    print("Failed to import necessary libraries after installation attempt.")
    print("Please ensure 'python-telegram-bot' is installed and 'flight_api_client.py' is accessible.")
    exit(1)


# --- Bot Configuration & Setup ---

# --- DEPLOYMENT NOTES ---
# To deploy this bot:
# 1. Set the TELEGRAM_BOT_TOKEN environment variable with your bot's API token.
#    Example: export TELEGRAM_BOT_TOKEN="your_actual_token_here"
# 2. Ensure Python and the `python-telegram-bot` library are installed on your server.
#    (The script attempts to install `python-telegram-bot` if missing, but it's better to manage dependencies explicitly in a deployment).
# 3. Run this script using a process manager (like systemd, supervisord, or a platform-specific one like Heroku dynos)
#    to ensure it runs continuously and restarts on failure.
# 4. Consider setting up proper logging instead of just print statements for production monitoring.
# 5. The flight data is currently mocked via `flight_api_client.py`. For real functionality,
#    `flight_api_client.py` would need to be updated to connect to a live flight data API.
# --- END DEPLOYMENT NOTES ---

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to get Telegram Bot Token
def get_telegram_token():
    """
    Retrieves the Telegram API token.
    For now, it uses a hardcoded token.
    Ideally, this should come from an environment variable.
    """
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        # Fallback to hardcoded token for current testing, with a warning
        logger.warning("Warning: TELEGRAM_BOT_TOKEN environment variable not set. Using hardcoded token. THIS IS NOT RECOMMENDED FOR PRODUCTION.")
        print("Warning: TELEGRAM_BOT_TOKEN environment variable not set. Using hardcoded token. THIS IS NOT RECOMMENDED FOR PRODUCTION.") # Also print for visibility
        token = "8098511672:AAEVyLLaxtFajj1S_0fIIYOghNhIiXXeMog" # The currently working token
    else:
        logger.info("Telegram token retrieved from environment variable.")

    if not token: # Should only happen if hardcoded token is also removed/empty
        logger.error("Critical: Telegram Bot Token is not available (neither env var nor hardcoded fallback).")

    return token

# --- Command Handlers ---
async def search_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /search command.
    Expected format: /search ORIGIN DESTINATION YYYY-MM-DD
    """
    logger.info(f"Received /search command from user {update.effective_user.name if update.effective_user else 'Unknown'}")

    # Retrieve user-specific threshold, fallback to global PRICE_THRESHOLD
    user_threshold = context.user_data.get('price_threshold', PRICE_THRESHOLD)
    logger.info(f"User {update.effective_user.id} using threshold: {user_threshold}")

    args = context.args
    if not args or len(args) != 3:
        usage_message = "Usage: /search <OriginCode> <DestinationCode> <YYYY-MM-DD>"
        await update.message.reply_text(usage_message)
        logger.warning(f"Invalid /search usage: {args}")
        return

    origin, destination, date_str = args[0].upper(), args[1].upper(), args[2] # Standardize airport codes to upper

    # Basic validation (can be expanded, e.g., date format, IATA code structure)
    # A simple regex could be used for date validation if needed: import re; if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str): ...
    if not (len(origin) == 3 and origin.isalpha() and \
            len(destination) == 3 and destination.isalpha() and \
            len(date_str) == 10): # Basic check, not full date validation
        await update.message.reply_text(
            "Invalid format for origin, destination, or date.\n"
            "Please use 3-letter IATA codes for airports and YYYY-MM-DD for date."
        )
        logger.warning(f"Invalid argument format for /search: O={origin}, D={destination}, Date={date_str}")
        return

    logger.info(f"Calling search_flights_api with: O={origin}, D={destination}, Date={date_str}")

    try:
        flights = search_flights_api(origin, destination, date_str) # From flight_api_client.py
    except Exception as e:
        logger.error(f"Error calling search_flights_api: {e}", exc_info=True)
        await update.message.reply_text("An internal error occurred while searching for flights.")
        return

    if flights is None: # search_flights_api might return None on error
        await update.message.reply_text(f"Error fetching flight data for {origin} to {destination} on {date_str}.")
        logger.error("search_flights_api returned None.")
        return

    if not flights: # Empty list
        await update.message.reply_text(f"No flights found for {origin} to {destination} on {date_str}.")
        logger.info("No flights found by API for the criteria.")
        return

    # Alert logic for cheap flights
    cheap_flights = []
    for flight in flights:
        try:
            # Assuming price from API (mocked) is already a float.
            # If it could be a string, conversion would be needed: float(flight.get('price', float('inf')))
            price = flight.get('price')
            if price is not None and price <= user_threshold: # Use user_threshold here
                cheap_flights.append(flight)
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting/comparing price for flight {flight.get('flight_number', 'Unknown')}: {e} - Price was: {flight.get('price')}")
            continue # Skip this flight if price is invalid

    if cheap_flights:
        alert_intro = f"ALERT! Found {len(cheap_flights)} cheap flight(s) (below ${user_threshold:.2f}) for {origin} to {destination} on {date_str}:\n" # Use user_threshold
        await update.message.reply_text(alert_intro)
        logger.info(f"Found {len(cheap_flights)} cheap flights for user {update.effective_user.id} below their threshold of ${user_threshold:.2f}. Sending alerts.")

        message_parts = []
        for flight in cheap_flights:
            flight_detail = (
                f"✈️ Airline: {flight.get('airline', 'N/A')}\n"
                f"   Flight: {flight.get('flight_number', 'N/A')}\n"
                f"   Price: ${flight.get('price', 0.0):.2f}\n"
                f"   Departs: {flight.get('departure_time', 'N/A')}"
            )
            message_parts.append(flight_detail)

        # Combine details into fewer messages if possible, respecting Telegram message length limits
        combined_message = ""
        for part in message_parts:
            if len(combined_message) + len(part) + 2 > 4096: # Telegram message length limit
                await update.message.reply_text(combined_message)
                combined_message = part + "\n\n"
            else:
                combined_message += part + "\n\n"

        if combined_message: # Send any remaining part
            await update.message.reply_text(combined_message)

    else: # No cheap flights, but there were flights
        regular_flights_message = f"Found {len(flights)} flights, but none below your threshold of ${user_threshold:.2f} for {origin} to {destination} on {date_str}.\n\n" # Use user_threshold
        # Optionally, list some of the regular priced flights if desired
        # For now, just inform that no cheap flights were found.
        # Example: list first 1-2 non-cheap flights
        # for flight in flights[:2]:
        #     regular_flights_message += (
        #         f"✈️ Airline: {flight.get('airline', 'N/A')}, Price: ${flight.get('price', 0.0):.2f}\n"
        #     )
        await update.message.reply_text(regular_flights_message)
        logger.info(f"No flights found below user {update.effective_user.id}'s threshold of ${user_threshold:.2f}. Total flights found: {len(flights)}.")

async def set_threshold_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /setthreshold command to set a user-specific price threshold."""
    logger.info(f"Received /setthreshold command from user {update.effective_user.name if update.effective_user else 'Unknown'}")
    args = context.args

    if not args or len(args) != 1:
        await update.message.reply_text("Usage: /setthreshold <amount>\nExample: /setthreshold 250.75")
        logger.warning(f"Invalid /setthreshold usage: {args}")
        return

    try:
        new_threshold = float(args[0])
        if new_threshold <= 0:
            await update.message.reply_text("Price threshold must be a positive amount.")
            logger.warning(f"User {update.effective_user.id} tried to set non-positive threshold: {new_threshold}")
            return

        context.user_data['price_threshold'] = new_threshold
        await update.message.reply_text(f"Your price alert threshold has been updated to ${new_threshold:.2f}.")
        logger.info(f"User {update.effective_user.id} set price threshold to {new_threshold:.2f}")

    except ValueError:
        await update.message.reply_text("Invalid amount. Please provide a number for the threshold (e.g., 250 or 199.99).")
        logger.warning(f"User {update.effective_user.id} provided invalid threshold value: {args[0]}")

async def search_month_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /searchmonth command.
    Expected format: /searchmonth ORIGIN DESTINATION YYYY-MM
    """
    logger.info(f"Received /searchmonth command from user {update.effective_user.name if update.effective_user else 'Unknown'}")
    args = context.args

    if not args or len(args) != 3:
        usage_message = "Usage: /searchmonth <OriginCode> <DestinationCode> <YYYY-MM>"
        await update.message.reply_text(usage_message)
        logger.warning(f"Invalid /searchmonth usage: {args}")
        return

    origin, destination, year_month_str = args[0].upper(), args[1].upper(), args[2]

    # Validation for airport codes and year_month_str
    if not (len(origin) == 3 and origin.isalpha()):
        await update.message.reply_text("Invalid Origin Airport Code. Must be 3 alphabetic characters (e.g., JFK).")
        logger.warning(f"Invalid origin code: {origin}")
        return
    if not (len(destination) == 3 and destination.isalpha()):
        await update.message.reply_text("Invalid Destination Airport Code. Must be 3 alphabetic characters (e.g., LAX).")
        logger.warning(f"Invalid destination code: {destination}")
        return
    if not re.match(r"^\d{4}-\d{2}$", year_month_str):
        await update.message.reply_text("Invalid Year-Month format. Please use YYYY-MM (e.g., 2024-12).")
        logger.warning(f"Invalid year-month format: {year_month_str}")
        return

    await update.message.reply_text(
        f"Searching for the cheapest flights from {origin} to {destination} in {year_month_str}... "
        "This may take a minute or two, as I'm checking every day of the month."
    )
    logger.info(f"Calling find_cheapest_flights_in_month with: O={origin}, D={destination}, Month={year_month_str}")

    try:
        # This function is expected to be synchronous in flight_api_client for now.
        # If it were async, we'd await it.
        cheapest_flights = find_cheapest_flights_in_month(origin, destination, year_month_str)
    except Exception as e:
        logger.error(f"Error calling find_cheapest_flights_in_month: {e}", exc_info=True)
        await update.message.reply_text("An internal error occurred while searching for the cheapest flights.")
        return

    if not cheapest_flights: # Handles None or empty list
        await update.message.reply_text(f"No flights found for {origin} to {destination} in {year_month_str}.")
        logger.info(f"No cheapest flights found by API for O={origin}, D={destination}, Month={year_month_str}")
        return

    # Construct and send the message for cheapest flights
    # Assuming cheapest_flights is a list of flight dicts, each including 'price' and 'date'
    min_price = cheapest_flights[0].get('price') # All flights in this list should have the same price

    response_message = (
        f"🎉 Hooray! The cheapest price found for {origin} to {destination} in {year_month_str} is ${min_price:.2f}.\n"
        f"Here are the flight(s) at this price:\n\n"
    )

    logger.info(f"Found {len(cheapest_flights)} cheapest flights for O={origin}, D={destination}, Month={year_month_str} at price ${min_price:.2f}")

    message_parts = []
    for flight in cheapest_flights:
        flight_detail = (
            f"🗓️ Date: {flight.get('date', 'N/A')}\n"
            f"✈️ Airline: {flight.get('airline', 'N/A')}\n"
            f"   Flight No: {flight.get('flight_number', 'N/A')}\n"
            f"   Price: ${flight.get('price', 0.0):.2f}\n" # Should be min_price
            f"   Departs: {flight.get('departure_time', 'N/A')}"
        )
        message_parts.append(flight_detail)

    # Combine details into messages, respecting Telegram message length limits
    current_message = response_message
    for i, part in enumerate(message_parts):
        if len(current_message) + len(part) + 2 > 4096: # Telegram message length limit
            await update.message.reply_text(current_message)
            current_message = part + "\n\n"
        else:
            current_message += part + "\n\n"

        # Safety break if there are too many flights to list to avoid spamming (e.g., > 10 messages)
        if i > 28 and len(message_parts) > 30 : # Approx 3 flights per message, limit to ~10 messages
             current_message += f"...and {len(message_parts) - (i+1)} more similar flights."
             break


    if current_message: # Send any remaining part
        await update.message.reply_text(current_message)


# --- Message Handlers ---
async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles non-command text messages by providing usage instructions."""
    logger.info(f"Received non-command message from user {update.effective_user.name if update.effective_user else 'Unknown'}. Replying with help text.")
    help_text = (
        "I'm a flight bot. Here's how to use me:\n"
        "  - `/search <Origin> <Destination> <YYYY-MM-DD>`\n"
        "    (Example: /search JFK LAX 2024-12-24)\n"
        "    Searches for flights on a specific date.\n\n"
        "  - `/searchmonth <Origin> <Destination> <YYYY-MM>`\n"
        "    (Example: /searchmonth JFK LAX 2024-12)\n"
        "    Finds the cheapest flights in a specific month.\n\n"
        "  - `/setthreshold <amount>`\n"
        "    (Example: /setthreshold 250.50)\n"
        "    Sets your price alert threshold for the /search command."
    )
    await update.message.reply_text(help_text)

# --- Main Bot Logic ---
def main():
    """Starts the Telegram bot."""
    TELEGRAM_BOT_TOKEN = get_telegram_token()
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM BOT TOKEN IS NOT SET. BOT CANNOT START.")
        return

    logger.info("Building application...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("search", search_command_handler))
    logger.info("/search command handler registered.")
    application.add_handler(CommandHandler("setthreshold", set_threshold_command_handler))
    logger.info("/setthreshold command handler registered.")
    application.add_handler(CommandHandler("searchmonth", search_month_command_handler))
    logger.info("/searchmonth command handler registered.")

    # Register message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))
    logger.info("Generic text message handler registered.")

    logger.info("Starting bot polling...")
    try:
        application.run_polling()
    except Exception as e:
        logger.critical(f"Bot crashed with error: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Bot script started.")
    main()
    logger.info("Bot script finished (or was interrupted).")
