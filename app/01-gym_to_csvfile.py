import os
import sys
import numpy as np
import pandas as pd
import time

try:
    root = os.path.dirname(os.path.realpath(__file__))
except:
    root = os.getcwd()

sys.path.append(os.path.join(root, '..'))

from fmi_mlc import fmi_gym
from fmi_mlc import get_default_parameter

def main():
    # Define simulation start date (aligned with weather file)
    start_time = pd.Timestamp('1994-01-01')

    # fmi_gym parameter
    FMI_NAME = 'data/v43/office_v43.fmu'
    parameter = {
        'seed': 1,
        'store_data': True,
        'fmu_step_size': 60 * 60,  # 1 hour
        'fmu_path': os.path.join(root, FMI_NAME),
        'fmu_start_time': 0,
        'fmu_final_time': 365 * 24 * 60 * 60,  # 1 year
        'observation_names': [
            'T_Block1_OfficeXSWX1f',
            'T_Block1_OfficeXSEX1f',
            'T_Block1_OfficeXNWX1f',
            'T_Block1_OfficeXNEX1f',
            'T_Block1_CorridorX1f',
            'T_Block2_OfficeXSWX2f',
            'T_Block2_OfficeXSEX2f',
            'T_Block2_OfficeXNWX2f',
            'T_Block2_OfficeXNEX2f',
            'T_Block2_CorridorX2f',
            'T_out',   # outside Temperature
            'Wind_Speed', 
            'Wind_Direction', 
            'DNI',
             'Electricity',
            'DistrictHeating',
            'DistrictCooling',
        ]
    }

    # Create simulation environment
    env = fmi_gym(parameter)
    done = False
    state = env.reset()

    print("Start simulation")
    time.sleep(0.5)

    while not done:
        state, reward, done, info = env.step([])

    print("Simulation complete.")

    # Copy simulation results
    res = env.data.copy(deep=True)

    # Convert time column to datetime
    res['timestamp'] = res['time'].apply(lambda x: start_time + pd.Timedelta(seconds=x))

    # Reorder columns: timestamp first
    cols = ['timestamp'] + [col for col in res.columns if col != 'timestamp']
    res = res[cols]

    # Save to CSV in a writable directory (current working directory)
    output_path = 'simulation_results-v42.csv'
    res.to_csv(output_path, index=False)
    print(f"Simulation data saved to {output_path}")

    env.close()

if __name__ == '__main__':
    main()
