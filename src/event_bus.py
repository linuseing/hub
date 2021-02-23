class EventBus:

    def __init__(self, core: 'Core'):
        self.core = core

    def fire(self):
        """Fire an event on the bus"""
        pass

    def listen(self):
        """listen for events on the bus"""
        pass

    def listen_once(self):
        pass

    async def wait_for(self):
        pass

    def remove_listener(self):
        pass
