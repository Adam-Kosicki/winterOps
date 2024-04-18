import folium
import mygeotab
import pandas as pd

# Set up Geotab environment
client = mygeotab.API(username='GeoTabRTI',
                      password='TxdotResearch59',
                      server='gov4.geotab.com',
                      database='tx_dot')
client.authenticate()

# Define vehicle names and IDs
vehicle_names = ['03300K']
vehicle_ids = ['b3F8C']

from_date = '2023-01-24 00:00:00.00Z'  # Start of time period
to_date = '2023-01-24 15:56:25Z'  # End of time period

# Define a function to get GPS records
def get_gps_records(device_id, from_date, to_date):
    results = client.get('LogRecord', search={
        'deviceSearch': {'id': device_id},
        'fromDate': from_date,
        'toDate': to_date,
        'resultsLimit': 500,  # Adjust as needed
        'include': ['dateTime', 'logTime', 'longitude', 'latitude']
    })
    return results

# Function to fetch status data from statusdatacode.py and process it
def fetch_and_process_status_data():
    status_data = client.get('StatusData',
                             search={'deviceSearch': {'id': vehicle_ids[0]}, 'fromDate': from_date, 'toDate': to_date})
    df_status_data = pd.DataFrame.from_records(status_data)
    alll = pd.concat([df_status_data, df_status_data.diagnostic.dropna().apply(pd.Series)], axis=1)
    filtered = alll.loc[:, ~alll.columns.duplicated(keep='last')]
    all_new = filtered[filtered["id"].isin(['DiagnosticAux1Id', 'DiagnosticAux2Id', 'DiagnosticAux3Id', 'DiagnosticAux4Id', 'DiagnosticIgnitionId'])]
    filtered_dummy = pd.get_dummies(all_new, columns=['id'])
    AUX_options = ['id_DiagnosticAux1Id', 'id_DiagnosticAux2Id', 'id_DiagnosticAux3Id', 'id_DiagnosticAux4Id', 'id_DiagnosticIgnitionId']
    for col in AUX_options:
        col_name = col + "_mod"
        if sum(filtered_dummy.columns == col) > 0:
            filtered_dummy[col_name] = filtered_dummy['data'] * filtered_dummy[col]
        else:
            filtered_dummy[col_name] = 0
    # Convert DataFrame to list of dictionaries
    return filtered_dummy.to_dict('records')

# Function to find the closest status record for each GPS record
def find_closest_status_record(gps_data, status_data):
    closest_status_records = []
    for gps_record in gps_data:
        gps_timestamp = gps_record['dateTime']
        closest_status_record = min(status_data, key=lambda x: abs(pd.Timestamp(x['dateTime']) - pd.Timestamp(gps_timestamp)))
        closest_status_records.append(closest_status_record)
    return closest_status_records

# Create HTML map with GPS data and status data
def create_map(gps_data, closest_status_records):
    # Process the data
    coordinates = [(record['latitude'], record['longitude']) for record in gps_data]

    # Create a map centered at the mean coordinates of the data
    map_center = [sum(x) / len(x) for x in zip(*coordinates)]
    mymap = folium.Map(location=map_center, zoom_start=10)

    # Add line segments connecting consecutive GPS points
    for i in range(len(coordinates) - 1):
        coord1 = coordinates[i]
        coord2 = coordinates[i + 1]

        gps_record = gps_data[i]
        status_record = closest_status_records[i]

        if status_record:
            # Construct popup message with all relevant data
            popup_message = f"Segment {i + 1}: <br>"
            for key, value in status_record.items():
                popup_message += f"{key}: {value}<br>"
            # Add more information from the GPS record if needed
            popup_message += f"GPS DateTime: {gps_record['dateTime']}<br>"

            # Determine line color based on status
            if status_record.get('id_DiagnosticAux4Id', False):
                line_color = "green"  # Set to green if id_DiagnosticAux4Id is true
            elif status_record.get('id_DiagnosticAux3Id', False):
                line_color = "blue"  # Set to blue if id_DiagnosticAux3Id is true
            else:
                line_color = "red" if status_record['data'] else "blue"


        line = folium.PolyLine([coord1, coord2], color=line_color, weight=2.5, opacity=1)
        folium.Popup(popup_message).add_to(line)
        line.add_to(mymap)

    # Save the map to an HTML file
    mymap.save('gps_data_map.html')
    print("Map saved as 'gps_data_map.html'.")

# Main function
def main():
    gps_data = get_gps_records(vehicle_ids[0], from_date, to_date)
    status_data = fetch_and_process_status_data()
    closest_status_records = find_closest_status_record(gps_data, status_data)
    create_map(gps_data, closest_status_records)

if __name__ == "__main__":
    main()
