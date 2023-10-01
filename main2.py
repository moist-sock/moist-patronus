import logging

from discord import Intents, LoginFailure, PrivilegedIntentsRequired, utils
from util.patronus_bot import PatronusBot


# Creates our bot object and sets any settings needed such as intents
def generate_bot():
    # In order for our bot to be member aware, we need to enable the members intent
    intents = Intents.all()
    intents.members = True

    bot = PatronusBot(command_prefix='!', intents=intents)

    return bot


def main():
    bot = generate_bot()

    # or, for example
    utils.setup_logging(level=logging.INFO, root=True)

    try:
        with open('config/token.txt', 'r') as f:
            token = f.read()
            logging.info("Using token in config/token.txt!")
    except FileNotFoundError as e:
        logging.warning("Could not find config/token.txt!")

    if not token:
        logging.fatal(
            f"ERROR: Failed to find a token! Either define the token as an environment variable using TOKEN or put "
            f"the token in config/token.txt!")
        exit(-1)

    # Attempt to log in, if we fail because of a bad token, let them know
    try:
        bot.run(token)
    except LoginFailure:
        logging.fatal(f"ERROR: An invalid token was given!")
        exit(-1)
    except PrivilegedIntentsRequired:
        logging.fatal(
            f"ERROR: Missing intentions required from generate_bot() method, you must enable these on the discord "
            f"developer portal for your bot!")


if __name__ == '__main__':
    main()
