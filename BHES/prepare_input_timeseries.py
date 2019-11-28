import pandas as pd
import sys

ts = pd.read_csv(sys.argv[1])

temperature = pd.read_csv(sys.argv[2], decimal=',', sep=';')

ts['heat_target'] = ts['heat-storage'].diff() * 1e6
ts['heat_target'] = ts['heat_target'].apply(
        lambda x: x / 1.1905 if x < 0 else x / 0.84)
ts.loc[0, 'heat_target'] = 0
ts['temperature_feed'] = temperature['Temperatur VL']
ts['temperature_return'] = temperature['Temperatur RL']
ts['pressure_feed'] = 9.5
ts['pressure_return'] = 10
ts = ts.drop(columns=['heat-storage'])
ts = ts.rename(columns={'timeindex': 'time'})
ts.set_index('time')
ts.to_csv('input_timeseries.csv', index=False)