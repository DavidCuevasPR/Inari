import yaml


def reload_config():
    global config
    with open("config.yaml") as fp:
        config = yaml.safe_load(fp)


config = None
reload_config()