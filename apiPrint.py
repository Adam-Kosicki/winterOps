import mygeotab

# Connect to the Geotab API
api = mygeotab.API(username='GeoTabRTI',
                   password='TxdotResearch59',
                   server='gov4.geotab.com',
                   database='tx_dot')

# Authenticate with the API
api.authenticate()

# Retrieve some data, for example, a list of devices
devices = api.get('Device')

# Print out the retrieved data
for device in devices:
    print(device)
