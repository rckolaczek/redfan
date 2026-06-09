import os
import json
import subprocess

def get_sensors(gpu_id=None):
    try:
        if os.name == 'posix':
            result = json.loads(subprocess.run(['sensors', '-j'], capture_output=True, text=True).stdout)
        elif os.name == 'nt':
            result = {} # Placeholder response for Windows | tbd
        else:
            raise Exception("Unsupported operating system")

        if gpu_id:
            return result.get(gpu_id, {})
    except Exception as e:
        print(f"Error fetching Intel GPU temperature using sensors: {e}")
    return result