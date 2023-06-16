import configparser


def parse_config():
    config = configparser.ConfigParser()
    config.read("termoline.ini")

    device_keys_list = [key for key in config.keys()][2:]

    types_and_names = [(value.split(',')[0], value.split(',')[1]) for value in config['userlist'].values()]

    formulas = {}
    for key in device_keys_list:
        formulas[key] = {key: (float(value.split('+')[0]), float(value.split('+')[1].split('*')[0])) for key, value in
                config[key].items()}

    return types_and_names, formulas



