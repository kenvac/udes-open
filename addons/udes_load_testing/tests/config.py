from odoo import tools
import ast



class Config(object):

    CONFIG_KEY = 'udes_load_test'

    DEFAULT_PARAMS = [(10,), (50,), (100,), (150,), (200,)]
    DEFAULT_REPEATS = 3
    DEFAULT_BACKGROUND = 100

    def __init__(self):
        super(Config, self).__init__()

        self._options = tools.config.misc.get(self.CONFIG_KEY, {})

        self.repeats = int(self._options.get('repeats', self.DEFAULT_REPEATS))

        self.params = self._options.get('default', self.DEFAULT_PARAMS)
        if isinstance(self.params, str):
            self.params = ast.literal_eval(self.params)
        self.params *= self.repeats

        self.default = self.params

        self.background = int(self._options.get('background',
                                                self.DEFAULT_BACKGROUND))

    def __getattribute__(self, attr_name, *args):
        try:
            return super(Config, self).__getattribute__(attr_name, *args)

        except AttributeError as e:
            if attr_name.lower() in self._options:

                repeats = int(self._options.get(
                    attr_name.lower() + '_repeats', self.repeats))

                value = ast.literal_eval(
                    self._options[attr_name.lower()]) * repeats

                # Make it show if we need it again it isn't recalulated
                self.__setattr__(attr_name, value)
                return value
            else:
                # It's up to the caller to pick the default it wants
                return None
        else:
            # If we can find it in options raise origonal error
            raise e

    def get_background_n(self, classname):
        return self._options.get(classname + "_background", self.background)


config = Config()
