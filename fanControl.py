import redfish
import keyring

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

# get the system
# response = REDFISH_OBJ.get("/redfish/v1/Systems/1", None)

# get the temp sensors
response = REDFISH_OBJ.get("/redfish/v1/Chassis/Self/Thermal", None).dict
temperatures = response.get('Temperatures', [])

# print the response
# print(response.dict)
# print(temperatures)

for temp in temperatures:
    print(f"Sensor Name: {temp['Name']}, Reading: {temp['ReadingCelsius']}°C")


REDFISH_OBJ.logout()