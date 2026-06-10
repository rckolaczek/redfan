# RedFan Project

RedFan is a Python-based fan control system that uses the Redfish API to monitor and adjust GPU temperatures, ensuring optimal cooling performance.

## Features

- Monitors GPU temperature using sensors.
- Adjusts fan modes based on predefined profiles.
- Utilizes the Redfish API for fan profile management.

## Getting Started

### Prerequisites

1. **Python** (version 3.8 or higher)
2. **Redfish API** (for server management)
3. **Keyring library** (for secure password storage)

### Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/redfan.git
cd redfan
pip install -r requirements.txt
```

### Configuration

1. **Create a configuration file** (`config.json`):

   ```json
   {
       "sensor_profile": {
           "gpu_name": "xe-pci-0300",
           "sensor_path": "pkg"
       },
       "fan_profile": {
           "Auto": "Default",
           "Half": "Default-Half",
           "Full": "Default-Full"
       }
   }
   ```

2. **Store Redfish credentials**:

   Use the Keyring library to store your Redfish login credentials:

   ```python
   import keyring

   keyring.set_password('redfish', 'admin', 'your_password')
   keyring.set_password('redfish', 'host', 'your_host')
   ```

### Usage

Run the main script to start monitoring and adjusting fan modes based on GPU temperature:

```bash
python main.py
```

## Files Overview

- **fanControl.py**: Contains functions for interacting with the Redfish API, loading configuration, and managing fan profiles.
- **config.json**: Configuration file specifying sensor paths and fan profiles.
- **gpuControl.py**: Handles GPU temperature evaluation using system sensors.
- **main.py**: Main script that integrates all components to monitor GPU temperatures and adjust fan modes.

## References

- [Redfish API Documentation](https://redfish.dmtf.org/documentation/)
- [Keyring Library](https://pypi.org/project/keyring/)

## Troubleshooting

1. **Missing Configuration File**:
   Ensure the `config.json` file is correctly placed in the project directory.

2. **Authentication Issues**:
   Verify that the Redfish credentials are correctly stored using the Keyring library.

3. **Unsupported Operating System**:
   The script currently supports POSIX-based systems (Linux, macOS). Windows support is a placeholder and needs further development.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.