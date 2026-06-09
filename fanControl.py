import sys
import json
import redfish
import keyring
import subprocess

login_account = 'admin'

# Retrieve the password from the keyring
password = keyring.get_password('redfish', login_account)
login_host = f'https://{keyring.get_password('redfish', 'host')}'

if not password:
    # If no password is stored in the keyring, prompt for one and store it
    password = input(f'Enter password for {login_account}: ')
    keyring.set_password('redfish', login_account, password)
if not login_host:
    login_host = input(f'Enter password for {login_host}: ')
    keyring.set_password('redfish', 'host', login_host)


# main
REDFISH_OBJ = redfish.redfish_client(base_url=login_host, username=login_account, \
                      password=password, default_prefix='/redfish/v1/')
REDFISH_OBJ.login(auth="session")

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

# change the active fan profile | dump to file
fan_profile = get_fan_profile(REDFISH_OBJ)
new_profile = 'Unraid-Default-GPU'
fan_profile['strMode'] = new_profile
with open('fan_profiles.json', 'w') as f:
    json.dump(fan_profile, f)

# import the new profile
headers = {'Content-Type': 'multipart/form-data'}
with open('fan_profiles.json', 'rb') as file_stream:
    payload = {
        'ImportFanprofile': ('fan_profiles.json', file_stream, 'application/octet-stream')
    }
    response = REDFISH_OBJ.post("/redfish/v1/Chassis/Self/Thermal/FanprofileService/Fanprofile", body=payload, headers=headers)



# print the response
# sys.stdout.write("%s\n" % response)
print(response)
# print(response.dict)
# print(temperatures)
# print(fan_profiles)

# print temperatures
# for temp in temperatures:
#     print(f"Sensor Name: {temp['Name']}, Reading: {temp['ReadingCelsius']}°C")

# # print fan profiles
# for policy in fan_profiles:
#     print(f"Profile Name: {policy['strName']}")


REDFISH_OBJ.logout()