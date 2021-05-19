import asyncio
import logging
from typing import Dict, List, Callable, Optional, Any

from paho.mqtt.client import Client, MQTTMessage

from objects.Context import Context
from objects.User import User
from plugin_api import plugin, run_after_init, output_service, input_service, formatter
from .constants import *


# scopes
PUBLISH = "mqtt.publish"

LOGGER = logging.getLogger("MQTT")


@plugin("mqtt")
class MQTT:
    def __init__(self, core, config: Dict = {}):
        self.core = core
        self.broker = (config["server_ip"], config["port"])
        self.credentials = (config["username"], config["password"])
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.event = asyncio.Event(loop=core.event_loop)
        self.event.clear()

        self.client: Client() = Client((config["client_id"] or DEFAULT_NAME))

        if config["username"] is not None:
            self.client.username_pw_set(config["username"], config["password"])

    @run_after_init
    async def setup(self):
        try:
            await self.core.async_add_job(
                self.client.connect, self.broker[0], self.broker[1], 60
            )
            self.client.loop_start()
            self.event.set()
        except Exception as e:
            LOGGER.error(f"there was an error setting up the MQTT connection ({e})")

    def add_subscription_callback(self, topic: str, callback: Callable):
        if topic in self.subscriptions:
            self.subscriptions[topic].append(callback)
        else:
            self.subscriptions[topic] = [callback]

        return lambda: self.subscriptions[topic].remove(callback)

    def new_context(self, topic: str):
        return Context(User.new_admin(), remote=True)

    def message_handler(self, msg: MQTTMessage):
        subscriber: List[Callable] = self.subscriptions.get(msg.topic, [])
        subscriber += self.subscriptions.get(SUBSCRIBE_ALL, [])

        context = self.new_context(msg.topic)

        for callback in subscriber:
            self.core.add_job(callback, msg, context)

    @input_service("mqtt.subscribe", None)
    def subscribe(self, callback: Callable, topic: str, qos: int = 0):
        """
        Subscribe to a topic
        :param callback:
        :param topic:
        :param qos:
        :return:
        """
        self.core.add_job(self.async_subscribe, topic, qos)
        return self.add_subscription_callback(topic, callback)

    async def async_subscribe(
        self, topic: str, qos=0, callback: Optional[Callable] = None
    ):
        await self.event.wait()
        self.core.add_job(self.client.subscribe, topic, qos)
        if callback:
            return self.add_subscription_callback(topic, callback)

    def publish(self, payload: Any, context: Context, topic: str, qos=0, retain=True):
        self.core.add_job(self.async_publish, payload, context, topic, qos, retain)

    @output_service("mqtt.publish", None, None)
    async def async_publish(
        self,
        payload: Any,
        context: Context,
        topic: str,
        qos: int = 0,
        retain: bool = True,
    ):
        """
        Publish a message over MQTT
        :param payload: msg payload
        :param context: context
        :param topic: topic
        :param qos: qos
        :param retain: retain
        :return:
        """
        if context.authorize(PUBLISH, "*"):
            await self.event.wait()
            self.core.add_job(self.client.publish, topic, payload, qos, retain)
