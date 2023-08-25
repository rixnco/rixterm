from filters import FilterBase


class NOP(FilterBase):
    """NOP filter"""
    NAME = "nop"

    def __init__(self, terminal, config):
        FilterBase.__init__(self,terminal,config)
        self.nop=config.get('nop') or ''
        

    def rx(self, text):
        return self.nop+text

    def tx(self, text):
        return self.nop+text

    def echo(self, text):
        return self.nop+text
