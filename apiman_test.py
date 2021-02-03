import logging
from apimgt.gateway import gateway as GW

def setup_logging(logfile, loglevel):
    """Logging function
    """
    # Just do Basic logging, this can be enhanced if required.
    logging.basicConfig(level=loglevel, filename=logfile, filemode='w',
        format="%(asctime)s:%(levelname)s:%(message)s")
    logging.info(f"**Script Started**")

def main():
    """Test Apiman's Management API.

    """
    apiman_ip = "192.168.239.104"
    apiman_un = "admin"             # Default is 'admin'
    apiman_pw = "admin123!"         # Default is 'admin123!'
    apiman_org = "to"

    logfile = "apiman_test.log"
    loglevel = "DEBUG"              # DEBUG ERROR WARNING INFO CRITICAL

    setup_logging(logfile, loglevel)

    api_gw = GW(apiman_ip, apiman_un, apiman_pw)

    result = api_gw.get_system("status")
    #print(result.json())
    result_jsn = result.json()
    if (result is None):
        logging.error(f"No system status data: {api_gw.ip}")
        exit(1)
    try:
        status = result_jsn["up"]
    except:
        logging.error(f"Problem Getting system 'up' status: {api_gw.ip}")
        exit(1)
    if (status is not True):
        logging.error(f"system status not True: {api_gw.ip}, {status}")
        exit(1)

    print(result_jsn["up"])
    # Create Organisation within Apiman to work with.
    result = api_gw.post_org(apiman_org)
    if (result is None):
        logging.error(f"Problem Posting Organisation: {apiman_org}")
        exit(1)

if __name__ == "__main__":
    main()