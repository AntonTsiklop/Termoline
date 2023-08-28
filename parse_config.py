import configparser


class ParseConfig:

    @staticmethod
    def parse_config():
        config = configparser.ConfigParser()
        config.read("termoline.ini")

        device_keys_list = [key for key in config.keys()][2:]

        types_and_names = [(value.split(',')[0], value.split(',')[1]) for value in config['userlist'].values()]

        formulas = {}
        for key in device_keys_list:
            if key != 'options':
                formulas[key] = {key: (float(value.split('+')[0]), float(value.split('+')[1].split('*')[0])) for key, value in
                                 config[key].items()}

        return types_and_names, formulas

    @staticmethod
    def config_write(com_num, amount):
        config = configparser.ConfigParser()
        config.read('termoline.ini')
        if 'options' not in config:
            config['options'] = {'com_num': com_num, 'amount': amount}
            with open('termoline.ini', 'w') as configfile:
                config.write(configfile)
        else:
            config['options'] = {'com_num': com_num, 'amount': amount}
            with open('termoline.ini', 'w') as configfile:
                config.write(configfile)

    @staticmethod
    def get_options():
        config_current = configparser.ConfigParser()
        config_current.read('termoline.ini')
        if 'options' in config_current:
            return config_current['options']['com_num'], config_current['options']['amount']
        return False

