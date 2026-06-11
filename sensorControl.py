# sensorControl.py
import os
import json
from pathlib import Path
import subprocess
import logging

logger = logging.getLogger(__name__)

# helpers
def get_local_path(path):
    """Get the local path of the current script."""
    path = Path(__file__).parent.resolve() / path
    return path

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

def get_sensors():
    try:
        if os.name == 'posix':
            result = json.loads(subprocess.run(['sensors', '-j'], capture_output=True, text=True).stdout, object_pairs_hook=combine_duplicate_keys)
        elif os.name == 'nt':
            # Placeholder response for Windows | place a test file in the script root if you want to evaluate
            with open(get_local_path("example.sensors.json")) as file:
                result = json.load(file, object_pairs_hook=combine_duplicate_keys)
            logger.info("Windows sensors not supported yet, evaluating anyway with a test file")
        else:
            logger.error("Unsupported operating system")
            raise
        logger.info(f"Successfully fetched sensor data")
    except Exception as e:
        logger.error(f"Error fetching sensors: {e}")
    return result

def evaluate_sensor_temperature(device_name, sensor_package, sensor_name, min_threshold=60, max_threshold=80, sensor_temp=None):
    try:
        fan_profile = 'Auto'
        sensors = get_sensors().get(device_name,{}).get(sensor_package,{})
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