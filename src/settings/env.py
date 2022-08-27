import environs


def create_env():
    dotenv = environs.Env()
    return dotenv


def load_dotenv(dotenv: bool):
    """Load environment from given file or dict."""
    if dotenv:
        env.read_env(".env")


def config_class(environment: str):
    """Link given environment to a config class."""
    return f"{__package__}.config.{environment.capitalize()}Config"


# the application environment
env = create_env()
