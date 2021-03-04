from paho.mqtt.client import MQTTMessage

from plugin_api import formatter


@formatter('mqtt.msg.get_payload')
def get_payload(_in: MQTTMessage):
    return _in.payload
