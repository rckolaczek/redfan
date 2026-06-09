# gpuControl.py
import os
import json
import subprocess
import logging

logger = logging.getLogger(__name__)

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
