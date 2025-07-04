"""
FMI-MLC main module.
"""

import os
import sys
import gym
import numpy as np
import pandas as pd

try:
    root = os.path.dirname(os.path.realpath(__file__))
except:
    root = os.getcwd()
sys.path.append(root)
from fmi_gym_parameter import get_default_parameter

class fmi_gym(gym.Env):
    '''Wrapper class for FMI-MLC'''

    def __init__(self, parameter={}, pyfmi=None):
        '''
        Setup the FMI-MLC gym environment.

        Inputs
        ------
        parameter (dict): Configuration dictionary, default see help(get_default_parameter).
        pyfmi (class): Specifies FMU handler, default None. None defaults to PyFMI package.
        '''
        super(fmi_gym, self).__init__()

        # Setup
        self.parameter = get_default_parameter()
        self.parameter.update(parameter)
        self.init = True

        # Parse Configuration
        self.seed_int = self.parameter['seed']
        self.precision = eval('np.{}'.format(self.parameter['precision']))
        self.parameter['fmu_observation_names'] = list(set(self.parameter['observation_names']) \
            - set(self.parameter['external_observations'].keys()))
        self.fmu_time = 0
        self.data = pd.DataFrame()
        self.data_all = []
        self.fmu_loaded = False
        self.fmu = None

        # FMI interface (load FMU)
        self.setup_pyfmi(pyfmi)

        # Use Python preprocessing before calling FMU
        if self.parameter['preprocessor']:
            self.preprocessor = self.parameter['preprocessor'](self.parameter)
        else:
            self.preprocessor = None

        # Use Python postprocessing after calling FMU
        if self.parameter['postprocessor']:
            self.postprocessor = self.parameter['postprocessor'](self.parameter)
        else:
            self.postprocessor = None

        # Use Python postprocessing after calling FMU
        if self.parameter['stateprocessor']:
            self.stateprocessor = self.parameter['stateprocessor'](self.parameter)
        else:
            self.stateprocessor = None

        # Function to process on reset
        if self.parameter['resetprocessor']:
            self.resetprocessor = self.parameter['resetprocessor'](self.parameter)
        else:
            self.resetprocessor = None

        # Use FMU model?
        if self.parameter['fmu_path']:
            self.use_fmu = True
        else:
            self.use_fmu = False

        self.action_space = gym.spaces.Box(low=self.parameter['action_min'],
                                           high=self.parameter['action_max'],
                                           shape=(len(self.parameter['action_names']), ),
                                           dtype=self.precision)

        self.observation_space = gym.spaces.Box(low=self.parameter['observation_min'],
                                                high=self.parameter['observation_max'],
                                                shape=(len(self.parameter['observation_names']), ),
                                                dtype=self.precision)

        if self.parameter['fmu_episode_duration']:
            self.episode_duration = self.parameter['fmu_episode_duration']
        else:
            action_start_time = self.parameter['fmu_warmup_time'] \
                if self.parameter['fmu_warmup_time'] else self.parameter['fmu_start_time']
            self.episode_duration = self.parameter['fmu_final_time'] \
                                    - action_start_time

        if self.parameter['reset_on_init']:
            self.state = self.reset()
        else:
            self.state = np.array([np.nan]*len(self.parameter['observation_names']))

    def setup_pyfmi(self, pyfmi):
        '''
        Setup PyFMI or custom handler.

        Inputs
        ------
        pyfmi (fun): Hander for fmu evaluation.
        '''
        if pyfmi != None:
            self.load_fmu = pyfmi
        else:
            try:
                from pyfmi import load_fmu
                self.load_fmu = load_fmu
            except Exception as e:
                print('ERROR: The "pyfmi" package was not found. Please install.')
                raise e

    def configure_fmu(self):
        '''
        Load and setup the FMU.

        Inputs
        ------
        ext_param (dict): External parameter outside of this class.
        start_time (float): Start time of the model, in sceonds.
        '''
        # Load FMU
        self.fmu = self.load_fmu(self.parameter['fmu_path'],
                                 log_level=self.parameter['fmu_loglevel'],
                                 kind=self.parameter['fmu_kind'])

        # Parameterize FMU
        param = self.parameter['fmu_param']
        param.update(self.parameter['inputs'])
        if param != {}:
            self.fmu.set(list(param.keys()), list(param.values()))

        # Initizlaize FMU
        self.fmu.setup_experiment(start_time=self.parameter['fmu_start_time'],
                                  stop_time=self.parameter['fmu_final_time'],
                                  stop_time_defined=False,
                                  tolerance=self.parameter['fmu_tolerance'])
        self.fmu.initialize()
        self.fmu_loaded = True

    def evaluate_fmu(self, inputs, advance_fmu=True):
        ''' evaluate the fmu '''
        if advance_fmu:
            inputs = inputs.copy()
            if self.parameter['inputs_map']:
                cols = {v:k for k,v in self.parameter['inputs_map'].items()}
                inputs = inputs.rename(columns=cols)
            del inputs['time']

            # Set inputs
            cols = [c for c in inputs.columns if c not in self.parameter['hidden_input_names']]
            values = inputs[cols].iloc[0].values
            for i in range(len(values)):
                self.fmu.set(cols[i], values[i])
                
            # Compute FMU
            step_size = inputs.index[0] - self.fmu_time
            try:
                self.fmu.do_step(current_t=self.fmu_time, step_size=step_size)
            except Exception as e:
                print('ERROR: Could not evaluate the FMU.')
                print('See log for more information (set "fmu_loglevel" >= 3).')
                print('Inputs:\n{}'.format(inputs))
                print('States:\n{}'.format(self.state))
                raise e

            # Results
            self.fmu_time = self.fmu.time
        names = self.parameter['fmu_observation_names'] \
            + self.parameter['hidden_observation_names'] \
            + self.parameter['reward_names']
        res = self.fmu.get(names)
        res = pd.Series(res, index=names)

        return res

    def step(self, action, advance_fmu=True):
        ''' do step '''

        # Get internal FMU inputs
        if advance_fmu:
            data = pd.DataFrame({'time': [self.fmu_time+self.parameter['fmu_step_size']]})
        else:
            data = self.data

        # Parse inputs
        action = pd.DataFrame([action], columns=self.parameter['action_names'])
        data = pd.concat([data, action], axis=1)
        data.index = data['time'].values

        # Compute preprocessing (if specified)
        if self.preprocessor:
            data = self.preprocessor.do_calc(data, self.init)

        # Evaluate FMU
        if self.use_fmu:
            res = self.evaluate_fmu(data, advance_fmu=advance_fmu)
            for k,v in res.items():
                data[k] = v
        else:
            if advance_fmu:
                self.fmu_time += self.parameter['fmu_step_size']

        # Compute postprocessing (if specified)
        if self.postprocessor:
            data = self.postprocessor.do_calc(data, self.init)

        # Compute reward
        if self.parameter['reward_names']:
            data['reward'] = data[self.parameter['reward_names']].sum(axis=1)
        elif 'reward' in data.columns:
            pass
        else:
            data['reward'] = -1

        # Outputs
        reward = data['reward'].values[0]
        info = {'data': data.to_json()}
        self.state = data[self.parameter['observation_names']].values[0]
        if self.stateprocessor:
            self.state = self.stateprocessor.do_calc(self.state, self.init)
        if self.fmu_time >= self.action_start_time + self.episode_duration:
            done = True
        else:
            done = False
        self.init = False
        if self.parameter['store_data']:
            if self.data.empty or not advance_fmu:
                self.data = data
            else:
                self.data = pd.concat([self.data, data])
            if self.parameter['store_all_data'] and done:
                self.data_all.append(self.data.copy(deep=True))

        return self.state, reward, done, info

    def reset(self):
        ''' reset environment '''

        if self.parameter['ignore_reset'] and self.fmu_loaded:
            # Ignore the reset command and continue with loaded FMU/states
            self.parameter['fmu_start_time'] += self.episode_duration
            self.parameter['fmu_final_time'] += self.episode_duration
            if self.parameter['fmu_warmup_time']:
                print('WARNING: Disabling "fmu_warmup_time" when "ignore_reset" is set.')
                self.parameter['fmu_warmup_time'] = None
        else:
            self.close()
            self.fmu_loaded = False            

        self.data = pd.DataFrame({'time': [0]}, index=[0])
        self.init = True
        if self.resetprocessor:
            self.data, self.parameter = \
                self.resetprocessor.do_calc(self.data, self.parameter, self.init)

        # Load FMU
        self.fmu_time = self.parameter['fmu_start_time']
        self.action_start_time = self.parameter['fmu_warmup_time'] \
            if self.parameter['fmu_warmup_time'] else self.parameter['fmu_start_time']
        if not self.fmu_loaded and self.parameter['init_fmu'] and self.use_fmu:
            self.configure_fmu()
        self.data['time'] = self.fmu_time
        action = np.array([0] * len(self.parameter['action_names']))
        self.state, _, _, info = self.step(action, advance_fmu=False)

        # Warmup
        if self.parameter['fmu_warmup_time']:
            while self.fmu_time < self.action_start_time:
                self.state, _, _, info = self.step(action)
            if not self.parameter['store_warmup']:
                self.data = self.data.iloc[-1:]

        # Standardize info keys to match step
        info = {
            'data': self.data.to_json()
        }

        return self.state, info


    def render(self):
        ''' render environment '''
        return False

    def close(self):
        ''' unload fmu here '''
        try:
            if self.fmu_loaded:
                self.fmu.terminate()
        except Exception as e:
            print(e)
        self.fmu = None
