from serial.tools import miniterm

class FilterBase(miniterm.Transform):
    def __init__(self, terminal, config):
        miniterm.Transform.__init__(self)
        self.terminal=terminal
        self.config=config

    def __call__(self):
        """Called by the miniterm library when the filter is actually used"""
        return self



class SendOnEnter(FilterBase):
    """Send text on enter"""
    NAME = "send_on_enter"

    def __init__(self, terminal, config):
        FilterBase.__init__(self,terminal,config)
        self._buffer=''

    def tx(self, text):
        _eol = '\r\n' if self.terminal.eol =='crlf' else '\r' if self.terminal.eol =='cr' else '\n'
        self._buffer += text
        if self._buffer.endswith(_eol):
            text = self._buffer
            self._buffer = ""
            return text
        return ""

