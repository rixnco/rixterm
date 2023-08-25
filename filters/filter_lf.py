from filters import FilterBase


class LF(FilterBase):
    """remove LF from input"""
    NAME = "lf"

    def __init__(self, terminal, config):
        FilterBase.__init__(self,terminal,config)
        

    def rx(self, text):
        text=text.replace('\n', '')
        return text

