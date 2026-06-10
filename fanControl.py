# fanControl.py
import sys
import json
import redfish
import keyring
import logging
from gpuControl import *

# logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),                        # Output to console
        logging.FileHandler("fan_control.log")          # Output to a shared file
    ]
)

def setup_logger():
    """Setup logger with a specific log level and format."""
    logger = logging.getLogger(__name__)
    if not logger.hasHandlers():  # To avoid adding multiple handlers
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger()

# authentication
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

# helpers
def get_odata_spec(REDFISH_OBJ):
    try:
        response = REDFISH_OBJ.get("/redfish/v1/JsonSchemas/GBTFanprofileService.v1_0_0.json", None)
        logger.info("Successfully fetched OData spec")
        return response
    except Exception as e:
        logger.error(f"Failed to fetch OData spec: {e}")
        return None

def get_system(REDFISH_OBJ):
    try:
        response = REDFISH_OBJ.get("/redfish/v1/Systems/1", None)
        logger.info("Successfully fetched system information")
        return response
    except Exception as e:
        logger.error(f"Failed to fetch system information: {e}")
        return None

def get_temp_sensors(REDFISH_OBJ):
    try:
        response = REDFISH_OBJ.get("/redfish/v1/Chassis/Self/Thermal", None).dict
        temperatures = response.get('Temperatures', [])
        logger.info(f"Successfully fetched temperature sensors: {len(temperatures)} found")
        return temperatures
    except Exception as e:
        logger.error(f"Failed to fetch temperature sensors: {e}")
        return []
    
def get_fan_mode(REDFISH_OBJ):
    try:
        response = REDFISH_OBJ.get("/redfish/v1/Chassis/Self/Thermal/FanprofileService/FanMode", None).dict
        logger.info("Successfully fetched fan mode")
        return response
    except Exception as e:
        logger.error(f"Failed to fetch fan mode: {e}")
        return {}

def get_fan_profile(REDFISH_OBJ):
    try:
        response = REDFISH_OBJ.get("/redfish/v1/Chassis/Self/Thermal/FanprofileService/Fanprofile", None).dict
        logger.info("Successfully fetched fan profile")
        return response
    except Exception as e:
        logger.error(f"Failed to fetch fan profile: {e}")
        return {}

def dump_fan_profile(REDFISH_OBJ, new_mode):
    try:
        fan_profile = get_fan_profile(REDFISH_OBJ)
        fan_profile['strMode'] = new_mode
        with open('fan_profile.json', 'w') as f:
            json.dump(fan_profile, f)
            logger.info(f"Dumped fan profile with mode: {new_mode}")
    except Exception as e:
        logger.error(f"Failed to dump fan profile: {e}")

def set_fan_mode(REDFISH_OBJ, new_mode):
    try:
        payload = {"FanMode": f"{new_mode}"}
        response = REDFISH_OBJ.post("/redfish/v1/Chassis/Self/Thermal/FanprofileService/FanMode/Actions/FanMode.SetFanMode", body=payload)
        logger.info("Successfully set fan mode")
        return response
    except Exception as e:
        logger.error(f"Failed to set fan mode: {e}")
        return None

def set_fan_profile(REDFISH_OBJ, profile_file):
    try:
        headers = {'Content-Type': 'multipart/form-data'}
        with open(profile_file, 'rb') as file_stream:
            payload = {
                'ImportFanprofile': ('fan_profiles.json', file_stream, 'application/octet-stream')
            }
            response = REDFISH_OBJ.post("/redfish/v1/Chassis/Self/Thermal/FanprofileService/Fanprofile", body=payload, headers=headers)
            logger.info("Successfully set fan profile")
        return response
    except Exception as e:
        logger.error(f"Failed to set fan profile: {e}")
        return None

def evaluate_gpu_temperature(gpu_name, sensor_path):
    try:
        fan_profile = 'Auto'
        gpuTemp = get_sensors(gpu_name).get(sensor_path)
        if gpuTemp is not None:
            logger.info(f"Evaluated GPU temperature for {gpu_name}: {gpuTemp}°C")
            if gpuTemp >= 65 and gpuTemp < 85:
                logger.info("Set fans to Half")
                fan_profile = 'Half'
            elif gpuTemp >= 85:
                logger.info("Set fans to Full")
                fan_profile = 'Full'
        else:
            logger.warning(f"No temperature data found for GPU sensor path: {sensor_path}")
            logger.info("Set fans to Auto")
    except Exception as e:
        logger.error(f"Failed to evaluate GPU temperature: {e}")
        logger.info("Set fans to Auto")
    finally:
        return fan_profile

# main
try:
    REDFISH_OBJ = redfish.redfish_client(base_url=login_host, username=login_account,
                      password=password, default_prefix='/redfish/v1/')
    REDFISH_OBJ.login(auth="session")
    logger.info("Successfully logged into Redfish server")


    # evaluate GPU | dump fan profile | update active profile settings | import new profile
    new_mode = evaluate_gpu_temperature('xe-pci-0300', 'pkg')
    if new_mode == 'Half':
        new_profile = 'Unraid-Default-GPU'
    elif new_mode == 'Full':
        new_profile = 'Unraid-Default-GPU'
    else:
        new_profile = 'Unraid-Default'
    dump_fan_profile(REDFISH_OBJ, new_profile)
    set_fan_profile(REDFISH_OBJ, 'fan_profiles.json')

    # # evaluate GPU | set fan mode
    # new_mode = evaluate_gpu_temperature('xe-pci-0300', 'pkg')
    # set_fan_mode(REDFISH_OBJ, new_mode)


except Exception as e:
    logger.error(f"Main execution failed: {e}")
finally:
    REDFISH_OBJ.logout()


