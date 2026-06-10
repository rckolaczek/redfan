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
            result = json.loads(subprocess.run(['sensors', '-j'], capture_output=True, text=True).stdout)
        elif os.name == 'nt':
            result = {} # Placeholder response for Windows | tbd
        else:
            raise Exception("Unsupported operating system")

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