import yaml


def load_yaml_config(
        yaml_file: str,
        values: dict
) -> dict:
    """
    Load configuration from a yaml file that uses jinja2 syntax
    """

    if yaml_file.split('.')[-1] not in ('yaml', 'yml'):
        raise ValueError('Only yaml or yml supported')

    with open(yaml_file) as file:
        content = file.read()

    return yaml.safe_load(content.format(**values))
