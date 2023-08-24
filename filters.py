from serial.tools import miniterm

class FilterBase(miniterm.Transform):
    def __init__(self, terminal):
        miniterm.Transform.__init__(self)
        self.terminal=terminal

    def __del__(self):
        self.terminal= None

    def __call__(self):
        """Called by the miniterm library when the filter is actually used"""
        return self



class SendOnEnter(FilterBase):
    """Send text on enter"""
    NAME = "send_on_enter"

    def __init__(self, terminal):
        FilterBase.__init__(self,terminal)
        self._buffer=''

    def tx(self, text):
        _eol = '\r\n' if self.terminal.eol =='crlf' else '\r' if self.terminal.eol =='cr' else '\n'
        self._buffer += text
        if self._buffer.endswith(_eol):
            text = self._buffer
            self._buffer = ""
            return text
        return ""

