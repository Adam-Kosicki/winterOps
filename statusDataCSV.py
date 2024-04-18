import mygeotab
import pandas as pd

# Define vehicle names and IDs
vehicle_names = ['03300K']
vehicle_ids = ['b3F8C']

from_date = '2023-01-24T15:00:00.000Z'  # Start of time period
to_date = '2023-02-01T16:00:00.000Z'  # End of time period

# Set up MyGeotab environment
client = mygeotab.API(username='GeoTabRTI',
                      password='TxdotResearch59',
                      server='gov4.geotab.com',
                      database='tx_dot')
client.authenticate()

# Define a function to get the device data
def get_device_data(device_id, from_date, to_date):
    results = client.get('StatusData',
                         search={'deviceSearch': {'id': device_id}, 'fromDate': from_date, 'toDate': to_date})
    return results

# Get status data for the specified vehicle and time period
device_id = vehicle_ids[0]  # Assuming only one vehicle ID is provided
status_data = get_device_data(device_id, from_date, to_date)

# Convert dictionary to DataFrame
df_status_data = pd.DataFrame.from_records(status_data)

# Unpack how the diagnostics appear from dictionary to string
alll = pd.concat([df_status_data, df_status_data.diagnostic.dropna().apply(pd.Series)], axis=1)

# There are 2 columns with title "id" this will keep the last one
filtered = alll.loc[:, ~alll.columns.duplicated(keep='last')]

# Only keep rows that have AUX records
all_new = filtered[filtered["id"].isin(['DiagnosticAux1Id', 'DiagnosticAux2Id', 'DiagnosticAux3Id', 'DiagnosticAux4Id', 'DiagnosticIgnitionId'])]

# Create dummy variables from the diagnostics
filtered_dummy = pd.get_dummies(all_new, columns=['id'])

# Rearrange the columns in a way to have 1 and 0s for each AUX
AUX_options = ['id_DiagnosticAux1Id', 'id_DiagnosticAux2Id', 'id_DiagnosticAux3Id', 'id_DiagnosticAux4Id', 'id_DiagnosticIgnitionId']

for col in AUX_options:
    col_name = col + "_mod"
    if sum(filtered_dummy.columns == col) > 0:
        filtered_dummy[col_name] = filtered_dummy['data'] * filtered_dummy[col]
    else:
        filtered_dummy[col_name] = 0

# Convert to CSV format
filtered_dummy.to_csv("STATUS_data.csv")
