import pandas as pd
import json
import time
from virtual_devices import simplePublisher as pub

def get_measurement_type(key):
    if key in ['Electricity', 'DistrictHeating', 'DistrictCooling']:
        return 'Power'
    elif key.startswith('T'):
        return 'Temperature'
    elif key.startswith('Wind'):
        return 'Wind'
    elif key in ['DHI', 'DNI', 'GHI']:
        return 'Solar_Radiation'
    elif 'shade' in key.lower():
        return 'Shade'
    else:
        return 'Other'

def main():
    # Load and check the CSV
    df = pd.read_csv('simulation_results.csv', parse_dates=['timestamp'])
    df.sort_values('timestamp', inplace=True)

    # Check timestamp interval
    df['interval'] = df['timestamp'].diff().dt.total_seconds()
    unique_intervals = df['interval'].dropna().unique()

    if len(unique_intervals) > 1 or unique_intervals[0] != 3600:
        print("⚠️ Warning: Timestamp intervals are not all 1 hour. Intervals found:", unique_intervals)

    df.drop(columns='interval', inplace=True)

    # Start the publisher
    publisher = pub.MyPublisher('Lab-Building')
    publisher.start()
    topic = 'virtual_building_send'

    print("🚀 Starting to publish data to Grafana...")

    for _, row in df.iterrows():
        timestamp = pd.to_datetime(row['timestamp']).isoformat()
        for key in df.columns:
            if key == 'timestamp' or key == 'time':
                continue

            value = row[key]
            if pd.isna(value):
                continue  # skip missing values

            measurement = get_measurement_type(key)

            payload = {
                "location": "MyBuilding",
                "measurement": measurement,
                "node": key,
                "time_stamp": timestamp,
                "value": str(value)
            }

            publisher.myPublish(topic, json.dumps(payload))
        
        time.sleep(0.1)  # optional: adjust to slow down if needed

    print("✅ All data published.")
    publisher.stop()

if __name__ == '__main__':
    main()
