class Env:
    use_ssh_config = None  # type: bool
    ssh_config = {}
    key_filename = None  # type: str
    port = None  # type: int
    user = None  # type: str
    password = None  # type: str
    hosts = []  # type: [str]
    host = None  # type: str
