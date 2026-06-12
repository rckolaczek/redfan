# fanControl.py
import os
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# helpers
@staticmethod
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

@staticmethod
def get_local_path(path):
    """Get the local path of the current script."""
    path = Path(__file__).parent.resolve() / path
    return path

@staticmethod
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

# FanController
class FanController:
    def __init__(self, redfish_obj):
        self.redfish_obj = redfish_obj

    def get_odata_spec(self):
        try:
            response = self.redfish_obj.get("/redfish/v1/JsonSchemas/GBTFanprofileService.v1_0_0.json", None)
            logger.info("Successfully fetched OData spec")
            return response
        except Exception as e:
            logger.error(f"Failed to fetch OData spec: {e}")
            return None

    def get_system(self):
        try:
            response = self.redfish_obj.get("/redfish/v1/Systems/1", None)
            logger.info("Successfully fetched system information")
            return response
        except Exception as e:
            logger.error(f"Failed to fetch system information: {e}")
            return None

    def get_temp_sensors(self):
        try:
            response = self.redfish_obj.get("/redfish/v1/Chassis/Self/Thermal", None).dict
            temperatures = response.get('Temperatures', [])
            logger.info(f"Successfully fetched temperature sensors: {len(temperatures)} found")
            return temperatures
        except Exception as e:
            logger.error(f"Failed to fetch temperature sensors: {e}")
            return []

    def get_fan_mode(self):
        try:
            response = self.redfish_obj.get("/redfish/v1/Chassis/Self/Thermal/FanprofileService/FanMode", None).dict
            logger.info("Successfully fetched fan mode")
            return response
        except Exception as e:
            logger.error(f"Failed to fetch fan mode: {e}")
            return {}

    def get_fan_profile(self):
        try:
            response = self.redfish_obj.get("/redfish/v1/Chassis/Self/Thermal/FanprofileService/Fanprofile", None).dict
            logger.info("Successfully fetched fan profile")
            return response
        except Exception as e:
            logger.error(f"Failed to fetch fan profile: {e}")
            return {}

    def dump_fan_profile(self, new_mode):
        try:
            fan_profile_path = get_local_path('fan_profile.json')
            fan_profile = self.get_fan_profile()
            fan_profile['strMode'] = new_mode
            with open(get_local_path(fan_profile_path), 'w') as f:
                json.dump(fan_profile, f)
                logger.info(f"Dumped fan profile to {fan_profile_path} with mode: {new_mode}")
                return fan_profile_path
        except Exception as e:
            logger.error(f"Failed to dump fan profile: {e}")

    def set_fan_mode(self, new_mode):
        try:
            payload = {"FanMode": f"{new_mode}"}
            response = self.redfish_obj.post("/redfish/v1/Chassis/Self/Thermal/FanprofileService/FanMode/Actions/FanMode.SetFanMode", body=payload)
            logger.info("Successfully set fan mode")
            return response
        except Exception as e:
            logger.error(f"Failed to set fan mode: {e}")
            return None

    def set_fan_profile(self, profile_path):
        try:
            headers = {'Content-Type': 'multipart/form-data'}
            with open(profile_path, 'rb') as file_stream:
                payload = {
                    'ImportFanprofile': ('fan_profile.json', file_stream, 'application/octet-stream')
                }
                response = self.redfish_obj.post("/redfish/v1/Chassis/Self/Thermal/FanprofileService/Fanprofile", body=payload, headers=headers)
                logger.info("Successfully set fan profile")
            return response
        except Exception as e:
            logger.error(f"Failed to set fan profile: {e}")
            return None

    def evaluate_fan_mode(self, config):
        try:
            redsense = SensorController()
            new_mode = redsense.evaluate_sensor_temperature(
                config.get('sensor_profile').get('device_name'),
                config.get('sensor_profile').get('sensor_package'),
                config.get('sensor_profile').get('sensor_name'),
                config.get('temp_profile').get('min'),
                config.get('temp_profile').get('max')
            )
            if config.get('fan_profile'):
                logger.info(f"Setting Fan Mode based on Custom profile: {new_mode}")
                new_profile = config.get('fan_profile').get(new_mode)
                old_profile = self.get_fan_profile().get('strMode',{})
                if old_profile != new_profile:
                    response = self.set_fan_profile(self.dump_fan_profile(new_profile))
                    return response
                else:
                    logger.info(f"Fan Mode is already set to: {new_mode}")
                    return {}
            else:
                logger.info(f"Custom fan profile is empty. Setting Fan Mode based on Default profile: {new_mode}")
                self.dump_fan_profile('default')
                self.set_fan_profile(self.dump_fan_profile(new_profile))
                response = self.set_fan_mode(new_mode)
                return response
        except Exception as e:
            logger.error(f"Failed to evaluate fan mode: {e}")

# SensorController
class SensorController:
    @staticmethod
    def combine_duplicate_keys(pairs):
        """
        Processes raw JSON key-value pairs during decoding.
        Groups duplicate keys into a single array list.
        """
        result = {}
        for key, value in pairs:
            if key in result:
                # If the value is not already a list, convert it into one
                if not isinstance(result[key], list):
                    result[key] = [result[key]]
                result[key].append(value)
            else:
                result[key] = value
        return result
    
    def get_sensors(self):
        try:
            if os.name == 'posix':
                result = json.loads(subprocess.run(['sensors', '-j'], capture_output=True, text=True).stdout, object_pairs_hook=self.combine_duplicate_keys)
            elif os.name == 'nt':
                # Placeholder response for Windows | place a test file in the script root if you want to evaluate
                with open(get_local_path("example.sensors.json")) as file:
                    result = json.load(file, object_pairs_hook=self.combine_duplicate_keys)
                logger.info("Windows sensors not supported yet, evaluating anyway with a test file")
            else:
                logger.error("Unsupported operating system")
                raise
            logger.info(f"Successfully fetched sensor data")
        except Exception as e:
            logger.error(f"Error fetching sensors: {e}")
        return result

    def evaluate_sensor_temperature(self, device_name, sensor_package, sensor_name, min_threshold=60, max_threshold=80, sensor_temp=None):
        try:
            fan_profile = 'Auto'
            sensors = self.get_sensors().get(device_name,{}).get(sensor_package,{})
            for i in sensors:
                if sensor_name in i:
                    sensor_temp = i.get(sensor_name,None)
                    break
            if sensor_temp:
                logger.info(f"Evaluated Device temperature for {sensor_name}: {sensor_temp}°C")
                if sensor_temp >= min_threshold and sensor_temp < max_threshold:
                    logger.info("Set fans to Half")
                    fan_profile = 'Half'
                elif sensor_temp >= max_threshold:
                    logger.info("Set fans to Full")
                    fan_profile = 'Full'
            else:
                logger.warning(f"No temperature data found for Device sensor path: {sensor_name}.{sensor_package}.{sensor_name}")
                logger.info("Set fans to Auto")
        except Exception as e:
            logger.error(f"Failed to evaluate Device temperature: {e}")
            logger.info("Set fans to Auto")
        finally:
            return fan_profile