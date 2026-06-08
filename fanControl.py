import sys
import json
import redfish
import keyring

# authentication
login_account = 'admin'
password = keyring.get_password('redfish', login_account)
login_host = f'https://{keyring.get_password('redfish', 'host')}'

if not password:
    # If no password is stored in the keyring, prompt for one and store it
    password = input(f'Enter password for {login_account}: ')
    keyring.set_password('redfish', login_account, password)
if not login_host:
    login_host = input(f'Enter password for {login_host}: ')
    keyring.set_password('redfish', 'host', login_host)

# helpers
def get_odata_spec(REDFISH_OBJ):
    response = REDFISH_OBJ.get("/redfish/v1/JsonSchemas/GBTFanprofileService.v1_0_0.json", None)
    return response

def get_system(REDFISH_OBJ):
    response = REDFISH_OBJ.get("/redfish/v1/Systems/1", None)
    return response

def get_temp_sensors(REDFISH_OBJ):
    response = REDFISH_OBJ.get("/redfish/v1/Chassis/Self/Thermal", None).dict
    temperatures = response.get('Temperatures', [])
    return temperatures

def get_fan_profile(REDFISH_OBJ):
    response = REDFISH_OBJ.get("/redfish/v1/Chassis/Self/Thermal/FanprofileService/Fanprofile", None).dict
    return response

def dump_fan_profile(REDFISH_OBJ, new_mode):
    fan_profile = get_fan_profile(REDFISH_OBJ)
    fan_profile['strMode'] = new_mode
    with open('fan_profiles.json', 'w') as f:
        json.dump(fan_profile, f)

def set_fan_profile(REDFISH_OBJ, profile_file):
    headers = {'Content-Type': 'multipart/form-data'}
    with open(profile_file, 'rb') as file_stream:
        payload = {
            'ImportFanprofile': ('fan_profiles.json', file_stream, 'application/octet-stream')
        }
        response = REDFISH_OBJ.post("/redfish/v1/Chassis/Self/Thermal/FanprofileService/Fanprofile", body=payload, headers=headers)
    return response


# main
REDFISH_OBJ = redfish.redfish_client(base_url=login_host, username=login_account, \
                      password=password, default_prefix='/redfish/v1/')
REDFISH_OBJ.login(auth="session")

# dump fan profile | update active profile | set new profile
new_mode = 'Unraid-Default-GPU'
dump_fan_profile(REDFISH_OBJ, new_mode)
set_fan_profile(REDFISH_OBJ, 'fan_profiles.json')
REDFISH_OBJ.logout()



# print the response | remove later
# sys.stdout.write("%s\n" % response)
# print(response)
# print(response.dict)
# print(temperatures)
# print(fan_profiles)

# print temperatures
# for temp in temperatures:
#     print(f"Sensor Name: {temp['Name']}, Reading: {temp['ReadingCelsius']}°C")

# # print fan profiles
# for policy in fan_profiles:
#     print(f"Profile Name: {policy['strName']}")