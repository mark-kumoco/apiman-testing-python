import logging
from apimgt.gateway import gateway as GW

def setup_logging():
    """Logging function
    """
    logfile = "apiman_test.log"
    loglevel = "DEBUG"              # DEBUG ERROR WARNING INFO CRITICAL
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

    setup_logging()

    api_gw = GW(apiman_ip, apiman_un, apiman_pw)

    api_gw.activate_availableplugins()
 
    api_gw.create_orgs()

    for org in api_gw.org_list:
        api_gw.create_apis(org)

    for org in api_gw.org_list:
        print(org.org_name)
        print(len(org.org_api_files))
        for y in org.org_api_files:
            print(y)
        for x in org.org_api_list:
            print(x)
    #result = api_gw.post_org(apiman_org)
    #if (result is None):
    #    logging.error(f"Problem Posting Organisation: {apiman_org}")
    #    exit(1)
    logging.info(f"**Script Finished**")

if __name__ == "__main__":
    main()