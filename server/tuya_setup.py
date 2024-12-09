import logging
import os
from dotenv import load_dotenv
from tuya_connector import (
    TuyaOpenAPI,
    TuyaOpenPulsar,
    TuyaCloudPulsarTopic,
    TUYA_LOGGER,
)

load_dotenv()

ACCESS_ID = os.getenv("ACCESS_ID")
ACCESS_KEY = os.getenv("ACCESS_KEY")
API_ENDPOINT = os.getenv("API_ENDPOINT")
MQ_ENDPOINT = os.getenv("MQ_ENDPOINT")

TUYA_LOGGER.setLevel(logging.DEBUG)

# Inicializa a API Tuya
def initialize_tuya_openapi():
    openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_KEY)
    openapi.connect()
    return openapi

# Inicializa o Pulsar (Websocket) e o listenr
def initialize_tuya_openpulsar(message_listener):
    open_pulsar = TuyaOpenPulsar(ACCESS_ID, ACCESS_KEY, MQ_ENDPOINT, TuyaCloudPulsarTopic.PROD)
    open_pulsar.add_message_listener(message_listener)
    open_pulsar.start()
    return open_pulsar
