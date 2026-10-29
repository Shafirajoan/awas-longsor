import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID", "awaslongsor_demo")
HOST = os.getenv("MQTT_HOST", "broker.hivemq.com")
PORT = int(os.getenv("MQTT_PORT", "8883"))
TLS = os.getenv("MQTT_TLS", "true").lower() == "true"
LAT = float(os.getenv("LAT", "-7.01"))
LON = float(os.getenv("LON", "110.41"))

def topic(suffix: str) -> str:
    return f"awaslongsor/{PROJECT_ID}/{suffix}"

def new_client(client_id: str) -> mqtt.Client:
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    if TLS:
        c.tls_set()
    return c