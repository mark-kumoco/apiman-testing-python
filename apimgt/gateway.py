import os
import sys
import os.path
import pathlib
import socket
import logging
import requests
import ipaddress
from os import path
from requests.auth import HTTPBasicAuth


class gateway (object):

    api_url_base = "/apiman/"
    api_url_orgs = "organizations/"
    api_url_systat = "system/status"
    ssl_verify = False
    ip = ""
    status = ""
    version = ""
    plugins = {}
    orgs = []
    orgs_dir = "orgs"

    def __init__(self, ip: str, un: str, pw: str, ssl_verify=False, **kwargs):
        """Set up Apiman GW variables and do some value/env checks.
        """
        self.un = un
        self.pw = pw

        self.check_ssl(ssl_verify)
        self.check_gw_ip(ip)

        self.api_url = f"https://{self.ip}:8443{self.api_url_base}"

        self.check_gw_status()

    def check_gw_status(self):
        """Is the Apiman status "up"? And extract the version of Apiman.

        If we have problems obtaining data, just exit.
        """
        gw_reponse = self.get_system("status")
        if (gw_reponse is None):
            logging.critical(f"No system status data: {self.ip} - is Apiman up? Correct credentials?")
            exit(1)
        try:
            self.status = gw_reponse["up"]
        except:
            logging.critical(f"Problem Getting system 'up' status: {self.ip}")
            exit(1)
        if (self.status is not True):
            logging.critical(f"system 'up' status not 'True': {self.ip}, {self.status}")
            exit(1)
        # Get Apiman Version:
        if (gw_reponse["version"] is None):
            logging.critical(f"No system version available from Apiman")
            exit(1)
        self.version = gw_reponse["version"]

        logging.debug(f"Apiman system summary: {self.ip},up={self.status},version={self.version}")

    def check_ssl(self, ssl_verify: bool):
        """Check SSL certs? If not, suppress warnings.
        """
        if ssl_verify is True:
            if os.path.isfile('/etc/ssl/certs/ca-certificates.crt'):
                self.ssl_verify = '/etc/ssl/certs/ca-certificates.crt'
            elif os.path.isfile('/etc/pki/tls/certs/ca-bundle.crt'):
                self.ssl_verify = '/etc/pki/tls/certs/ca-bundle.crt'
            else:
                raise Exception("No CA Certs file found")

        if not self.ssl_verify:
            requests.packages.urllib3.disable_warnings(                         # pylint: disable=no-member
                requests.packages.urllib3.exceptions.InsecureRequestWarning)    # pylint: disable=no-member

    def check_gw_ip(self, ip: str):
        """Check the submitted IP/DNS name is valid.
        Exit if nothing good is found.
        """
        try:
            self.ip = ipaddress.ip_address(ip)
        except ValueError:
            try:
                self.ip = socket.gethostbyname(ip)
            except:
                logging.error(f"Cannot translate {ip} to IP address")
                exit(1)
        except:
            logging.error(f"Error with IP/DNS value : {ip}")
            exit(1)

    def get_data(self, api_endp: str):
        """GET data from Apiman via REST. Returns JSON.

        Expect a 200 status for success.
        """
        logging.debug(f"GET URL:{self.api_url}{api_endp}")
        try:
            result = requests.get(
                    f"{self.api_url}{api_endp}",
                    auth=HTTPBasicAuth(self.un, self.pw),
                    verify=self.ssl_verify
                )
        except:
            logging.debug(f"GET Problem: {self.api_url}{api_endp}")
            return None
        # 200 means good
        if result.status_code != 200:
            logging.warning(f"GET result.status_code={result.status_code} @{self.api_url}{api_endp}")
            return None

        try:
            result = result.json()
            logging.debug(f"JSON:{result}")
        except:
            logging.error(f"RESPONSE is not JSON-able.")
            result = None

        return result

    def post_data(self, api_endp: str, jsn: dict):
        """POST data to Apiman via REST.

        Expect a 200 status for success, a 409 if data already exists beforehand.
        A warning is logged if neither of the above codes are returned.
        
        A 409 status code may be require further action, either programatically, or manually.
        At the moment, only an additional log is generated.
        """
        logging.debug(f"POST URL:{self.api_url}{api_endp}")
        try:
            result = requests.post(
                    f"{self.api_url}{api_endp}",
                    auth=HTTPBasicAuth(self.un, self.pw),
                    json = jsn,
                    verify=self.ssl_verify
                )
        except:
            logging.debug(f"POST Problem: {self.api_url}{api_endp} with '{jsn}'")
            return None

        # 200 means good POST, 409 means POST Conflict (object exists already, most likely).
        # If neither of those return, log warning.
        if result.status_code != 200 and result.status_code != 204 and result.status_code != 409:
            logging.warning(f"POST result.status_code={result.status_code} @{self.api_url}{api_endp}")
        # 409 may be ok. Log if received though.
        elif result.status_code == 409:
            logging.info(f"STATUS CODE NOT 200: result.status_code={result.status_code} @{self.api_url}{api_endp}")
            logging.debug(f"JSON:{jsn}")

        logging.debug(f"RESULT:{result}")

        return result

    def get_system(self, sys_item: str):
        """GET Apiman system data.

        A wrapper to get_data().
        """
        sys_item = f"system/{sys_item}"
        result = self.get_data(sys_item)
        if (result == False):
            return None
        return result

    def create_orgs(self):
        """POST Apiman organisation data. Check "org" dir for organisations.

        A wrapper to post_data().
        """
        if (not path.isdir(self.orgs_dir)):
            logging.critical(f"Not a directory: {self.orgs_dir}")
            exit()
        try: # pathlib.Path does not pass error to try...?
            orgs = pathlib.Path(self.orgs_dir).iterdir()
        except:
            logging.critical(f"Error with {self.orgs_dir}")
            exit()
        logging.debug(f"contents:{orgs}")

        for org in orgs:
            jsn = {
                        "name":os.path.basename(org),
                        "description":f"A logical container for {org}"
                    }
            result = self.post_data(self.api_url_orgs, jsn)
            if (result == False):
                return None
            self.orgs.append(org)
            


        print(f"%%%%{self.orgs}")
        return result

    def install_plugin(self, plugin: str):
        """Try to install default plugins.
        """
         # Now do the activation
        jsn = {
            "version":self.version,
            "groupId":"io.apiman.plugins",
            "artifactId":plugin,
            "type": "war"
        }
        logging.debug(f"---install_plugin----")
        logging.debug(f"JSON:{jsn}")
        result = self.post_data(f"plugins", jsn)
        if (result == None):
            logging.error(f"Error with plugin upgrade")
        if result.status_code != 200:
            logging.debug(f"NON 200 status with plugin upgrade status '{plugin}'', possibly installed already?")
        else:
            logging.debug(f"Plugin Upgraded {plugin}")
        #return result

    def activate_availableplugins(self):
        """Try to install default plugins.
        """
        sys_item = f"plugins/availablePlugins"
        all_plugins = self.get_data(sys_item)
        if (all_plugins == False):
            logging.debug(f"No Plugins found")
            return None

        for plugin in all_plugins:
            if plugin["version"] != self.version:
                logging.debug(f"Plugin version ({plugin['version']}) different from system version: ")
            self.install_plugin(plugin["artifactId"])
