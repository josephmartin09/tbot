import logging

from tbot.util import log

from . import api


def main():
    """Application entry point."""
    # Enable logging
    log.setup_logging()
    log.disable_sublogger("urllib3")

    # Pass configuration to the application
    # TODO
    logging.debug("Launching main application")

    api.run()


if __name__ == "__main__":
    main()
