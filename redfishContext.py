#redfishContext.py
import redfish
import logging

logger = logging.getLogger(__name__)

class RedfishContext:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.redfish_obj = None

    def __enter__(self):
        self.redfish_obj = redfish.redfish_client(
            base_url=self.base_url,
            username=self.username,
            password=self.password,
            default_prefix='/redfish/v1/'
        )
        self.redfish_obj.login(auth="session")
        logger.info("Successfully logged into Redfish server")
        return self.redfish_obj

    def __exit__(self, exc_type, exc_value, traceback):
        if self.redfish_obj:
            self.redfish_obj.logout()