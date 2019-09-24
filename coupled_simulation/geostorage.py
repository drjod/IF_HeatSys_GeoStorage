import os
from logging import info, error
from json import load
from subprocess import call
from abc import ABC, abstractmethod


class GeoStorageSimulator(ABC):
    @abstractmethod
    def preprocess(self):
        pass
    @abstractmethod
    def run(self):
        pass
    @abstractmethod
    def postprocess(self):
        pass


class OgsKb1(GeoStorageSimulator):
    def __init__(self, data):
        self.__data = data

    def preprocess(self, T_ff_sto, m_sto, storage_mode):
        """
        - write input files for geostorage simulation
        - Requirements:
            - _*.st prepared with keywords $WARM, $COLD for input / output source terms
            -  *.bc prepared with keywords $TYPE, $VALUE for boundary condition at inlet
        :param T_ff_sto: feed flow temperature to geostorage  (in *.bc )
        :param m_sto: (float) mass flow rate through heat exchanger at geostorage side (in *.st)
        :param storage_mode: (str) 'charging' or 'discharging'
        :return:
        """
        density = 1000

        directory = os.path.dirname(self.__data['simulation_files'])
        basename =  os.path.basename(self.__data['simulation_files'])
        if storage_mode == 'charging':
            # ST
            os.system("sed 's/$WARM/{0}/g' {1}/_{2}.st > {1}/{2}.st".format(m_sto / density, directory, basename))
            os.system("sed -i 's/$COLD/{}/g' {}/{}.st".format(-m_sto / density, directory, basename))
            # BC
            os.system("sed 's/$TYPE/WARM/g' {0}/_{1}.bc > {0}/{1}.bc".format(directory, basename))
            os.system("sed -i 's/$VALUE/{}/g' {}/{}.bc".format(T_ff_sto, directory, basename))

        elif storage_mode == 'discharging':
            # ST
            os.system("sed 's/$WARM/{0}/g' {1}/_{2}.st > {1}/{2}.st".format(-m_sto / density, directory, basename))
            os.system("sed -i 's/$COLD/{}/g' {}/{}.st".format(m_sto / density, directory, basename))
            # BC
            os.system("sed 's/$TYPE/COLD/g' {0}/_{1}.bc > {0}/{1}.bc".format(directory, basename))
            os.system("sed -i 's/$VALUE/{}/g' {}/{}.bc".format(T_ff_sto, directory, basename))

    def run(self):
        """
        - call geostorage simulator after file preparation
        :return:
        """
        os.system('touch {}'.format(os.path.dirname(self.__data['simulation_files']) + '/out.txt'))  # file must exist
        os.system('touch {}'.format(os.path.dirname(self.__data['simulation_files']) + '/error.txt'))  # file must exist
        call([self.__data['simulator_file'], self.__data['simulation_files']],
             stdout=open(os.path.dirname(self.__data['simulation_files']) + '/out.txt'),
             stderr=open(os.path.dirname(self.__data['simulation_files']) + '/error.txt'))
        info('GEOSTORAGE calculation completed')

    def postprocess(self, storage_mode):
        """
        evaluate result
        :param storage_mode: (string) 'charging' or 'discharging'
        :return: return flow temeprature from geostorage
        """
        well = 'COLD' if storage_mode == 'charging' else 'WARM'
        directory = os.path.dirname(self.__data['simulation_files'])
        try:
            with open('{}/testCase_time_{}.tec'.format(directory, well)) as file:
                line = file.readlines()[4]
                t_rf_sto = float(line.split()[1])
        except:
            t_rf_sto = None
        return t_rf_sto


class GeoStorage:
    def __init__(self, cd):
        info('GEOSTORAGE Reading input file .geostorage_ctr.json')
        path = (cd.working_dir + cd.geostorage_path + cd.scenario + '.geostorage_ctrl.json')
        # print(path)
        self.__specification = dict()
        with open(path) as file:
            self.__specification.update(load(file))

        if self.__specification['simulator_name'] == 'ogs_kb1':
            info('GEOSTORAGE simulator is OGS_kb1')
            self.__simulator = OgsKb1({'simulator_file': self.__specification['simulator_file'],
                                        'simulation_files': self.__specification['simulation_files']})
        else:
            error('GEOSTORAGE simulator not supported')
            self.__simulator = None
        # print(self.__specification)

    def simulation_files(self):
        return self.__specification['simulation_files']

    def run_storage_simulation(self, T_ff_sto, m_sto, storage_mode):
        """

        :param T_ff_sto: (float) feed flow temperature to geostorage
        :param m_sto: (float) mass flow rate through heat exchanger at geostorage side
        :param storage_mode: (str) 'charging' or 'discharging'
        :return: return flow temperature from geostorage
        """
        self.__simulator.preprocess(T_ff_sto, m_sto, storage_mode)
        self.__simulator.run()
        T_rf_sto = self.__simulator.postprocess(storage_mode)

        return T_rf_sto