# main.py
import sys
import keyring
from fanControl import *
from logging import handlers
from redfishContext import RedfishContext

# logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
    logging.StreamHandler(),                                # output to console
    handlers.RotatingFileHandler(
            get_local_path(path="redfan.log"),
            maxBytes=5000000,
            backupCount=3,
            encoding="utf-8"
        )                                                   # output to a rotating file in the script's execution directory
    ]
)
logger = setup_logger()

# authentication setup
login_account = 'admin'
password = keyring.get_password('redfish', login_account)
login_host = keyring.get_password('redfish', 'host')
login_url = f"https://{login_host}"

# prompt user for credentials if they do not exist
try:
    if not password:
        password = input(f'Enter password for {login_account}: ')
        keyring.set_password('redfish', login_account, password)
    if not login_host:
            login_host = input(f'Enter host for redfish: ')
            keyring.set_password('redfish', 'host', login_host)

except Exception as e:
    logger.error(f"Authentication setup failed: {e}")
    sys.exit(1)

# main
def main():
    try:
        # custom configuration for fan profiles, sensors, and temperature thresholds in your environment
        custom_config = load_config('config.json')
        # redfish connection manager
        with RedfishContext(login_url, login_account, password) as REDFISH_OBJ:
            # evaluate fan mode based on your custom config
            redfan = FanController(REDFISH_OBJ)
            redfan.evaluate_fan_mode(config=custom_config)

    except Exception as e:
        logger.error(f"Main execution failed: {e}")
if __name__ == "__main__":
    main()