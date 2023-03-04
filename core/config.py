import confuse

class ScruffyConfig(confuse.Configuration):
    def config_dir(self):
        return './'

config = ScruffyConfig('scruffy', __name__)