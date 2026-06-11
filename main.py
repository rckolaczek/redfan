import sys
import keyring
import redfish
from fanControl import *

# logging
log_dir = Path(__file__).parent.resolve()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),                        # Output to console
        logging.FileHandler(log_dir / "redfan.log")     # Output to a file in the script's execution directory
    ]
)
logger = setup_logger()

# authentication setup
login_account = 'admin'
password = keyring.get_password('redfish', login_account)
login_host = f'https://{keyring.get_password('redfish', 'host')}'

try:
    if not password:
        # If no password is stored in the keyring, prompt for one and store it
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
        # custom configuration for fan profile and temperature sensor path in your environment
        custom_config = load_config('config.json')

        # authenticate to Redfish server 
        REDFISH_OBJ = redfish.redfish_client(base_url=login_host, username=login_account,
                        password=password, default_prefix='/redfish/v1/')
        REDFISH_OBJ.login(auth="session")
        logger.info("Successfully logged into Redfish server")

        # evaluate GPU temperatures | evaluate fan modes | dump and update fan profile | import new profile and/or set new mode
        evaluate_fan_mode(REDFISH_OBJ, custom_config)

    except Exception as e:
        logger.error(f"Main execution failed: {e}")
    finally:
        REDFISH_OBJ.logout()

if __name__ == "__main__":
    main()