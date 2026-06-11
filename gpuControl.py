# gpuControl.py
import os
import json
import subprocess
import logging

logger = logging.getLogger(__name__)

# helpers
def get_sensors(gpu_id=None):
    try:
        if os.name == 'posix':
            result = json.loads(subprocess.run(['sensors', '-j'], capture_output=True, text=True).stdout, object_pairs_hook=parse_duplicates)
            # Flatten and extract every sub-value safely
            for root_key, contents in result:
                print(f"Device: {root_key}")
                for sub_key, sub_value in contents:
                    # Check if the sub_value is nested (like the temp/energy dicts)
                    if isinstance(sub_value, list):
                        for metric_key, metric_val in sub_value:
                            print(f"  [{sub_key}] {metric_key}: {metric_val}")
                    else:
                        print(f"  {sub_key}: {sub_value}")
        elif os.name == 'nt':
            result = {} # Placeholder response for Windows | tbd
            logger.info("Windows sensors not supported yet, evaluating anyway")
        else:
            logger.error("Unsupported operating system")
            raise

        logger.info(f"Successfully fetched sensor data")
        if gpu_id:
            return result.get(gpu_id, {})
    except Exception as e:
        logger.error(f"Error fetching sensors: {e}")
    return {}

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
    
def parse_duplicates(pairs):
    """Recursively parses json without letting duplicate keys overwrite each other."""
    return pairs