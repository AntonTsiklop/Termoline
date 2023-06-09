import configparser


def parse_config():
    config = configparser.ConfigParser()
    config.read("termoline.ini")

    types_and_names = [(value.split(',')[0], value.split(',')[1]) for value in config['userlist'].values()]

    formulas = {key: (float(value.split('+')[0]), float(value.split('+')[1].split('*')[0])) for key, value in
                config['Tz'].items()}

    return types_and_names, formulas
