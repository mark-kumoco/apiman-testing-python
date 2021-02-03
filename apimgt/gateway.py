import os
import sys
import socket
import logging
import requests
import ipaddress
from requests.auth import HTTPBasicAuth

class gateway (object):

    api_url_base = "/apiman/"
    api_url_orgs = "organizations/"
    api_url_systat = "system/status"
    ssl_verify = False
    ip = ""

    def __init__(self, ip: str, un: str, pw: str, ssl_verify=False, **kwargs):
        """Set up Apiman GW variables and do some value/env checks.
        """
        self.un = un
        self.pw = pw

        self.check_ssl(ssl_verify)
        self.check_gw_ip(ip)

        self.api_url = f"https://{self.ip}:8443{self.api_url_base}"

    def check_ssl(self, ssl_verify):
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

    def check_gw_ip(self, ip):
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
        """GET data from Apiman via REST.

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
            return False

        # 200 means good
        if result.status_code != 200 and result.status_code != 204 and result.status_code != 409:
            logging.warning(f"GET result.status_code={result.status_code} @{self.api_url}{api_endp}")

        logging.debug(f"RESULT:{result}")

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
            return False

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

    def post_org(self, orgName: str):
        """POST Apiman organisation data.

        A wrapper to post_data().
        """
        jsn = {
                    "name":orgName,
                    "description":f"A logical container for {orgName}"
                }
        result = self.post_data(self.api_url_orgs, jsn)
        if (result == False):
            return None
        return result