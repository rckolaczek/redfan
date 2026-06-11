# fanControl.py
import json
import logging
from pathlib import Path
from gpuControl import *

logger = logging.getLogger(__name__)


# helpers
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

def load_config(file_path: str) -> dict:
    """
    Loads a JSON config file. If a relative path is given, 
    it searches relative to the script's directory.
    """
    provided_path = Path(file_path)
    
    # Check if the user provided an absolute/full path
    if provided_path.is_absolute():
        final_path = provided_path
    else:
        final_path = get_local_path(provided_path)

    logger.info(f"Looking for configuration file at: {final_path}")
    
    if not final_path.exists():
        logger.error(f"Configuration file does not exist: {final_path}")
        raise FileNotFoundError(f"Missing config file: {final_path}")
        
    try:
        with open(final_path, "r", encoding="utf-8") as file:
            config_data = json.load(file)
            logger.info("Configuration file loaded successfully.")
            return config_data
            
    except json.JSONDecodeError as error:
        logger.error(f"Invalid JSON syntax in config file: {error}")
        raise

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
        fan_profile_path = get_local_path('fan_profile.json')
        fan_profile = get_fan_profile(REDFISH_OBJ)
        fan_profile['strMode'] = new_mode
        with open(get_local_path(fan_profile_path), 'w') as f:
            json.dump(fan_profile, f)
            logger.info(f"Dumped fan profile to {fan_profile_path} with mode: {new_mode}")
            return fan_profile_path
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

def set_fan_profile(REDFISH_OBJ, profile_path):
    try:
        headers = {'Content-Type': 'multipart/form-data'}
        with open(profile_path, 'rb') as file_stream:
            payload = {
                'ImportFanprofile': ('fan_profile.json', file_stream, 'application/octet-stream')
            }
            response = REDFISH_OBJ.post("/redfish/v1/Chassis/Self/Thermal/FanprofileService/Fanprofile", body=payload, headers=headers)
            logger.info("Successfully set fan profile")
        return response
    except Exception as e:
        logger.error(f"Failed to set fan profile: {e}")
        return None
    
def evaluate_fan_mode(REDFISH_OBJ, config):
    try:
        new_mode = evaluate_gpu_temperature(
            config.get('sensor_profile').get('gpu_name'),
            config.get('sensor_profile').get('sensor_package'),
            config.get('sensor_profile').get('sensor_name')
        )
        if config.get('fan_profile'):
            logger.info(f"Setting Fan Mode based on Custom profile: {new_mode}")
            new_profile = config.get('fan_profile').get(new_mode)
            response = set_fan_profile(REDFISH_OBJ, dump_fan_profile(REDFISH_OBJ, new_profile))
            return response
        else:
            logger.info(f"Custom fan profile is empty. Setting Fan Mode based on Default profile: {new_mode}")
            dump_fan_profile(REDFISH_OBJ, 'default')
            set_fan_profile(REDFISH_OBJ, dump_fan_profile(REDFISH_OBJ, new_profile))
            response = set_fan_mode(REDFISH_OBJ, new_mode)
            return response
    except Exception as e:
        logger.error(f"Failed to evaluate fan mode: {e}")
