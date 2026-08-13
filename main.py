from fastapi import FastAPI
from datetime import datetime
import secrets

app = FastAPI(
    title="MCOE Hotspot Server",
    version="1.0.0"
)

devices = {}


@app.get("/")
def root():
    return {
        "name": "MCOE Hotspot Server",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "server": "MCOE Hotspot Server"
    }


@app.post("/api/login")
def login(username: str, password: str):

    if username == "mcoe" and password == "mcoe":
        return {
            "success": True,
            "access_token": secrets.token_urlsafe(32)
        }

    return {
        "success": False,
        "message": "Invalid username or password"
    }


@app.post("/api/device/register")
def register_device(
    device_id: str,
    device_name: str
):

    token = secrets.token_urlsafe(32)

    devices[device_id] = {
        "device_id": device_id,
        "device_name": device_name,
        "device_token": token,
        "online": True,
        "last_seen": datetime.utcnow().isoformat(),
        "hotspot": False,
        "connected_clients": 0,
        "rx_bytes": 0,
        "tx_bytes": 0
    }

    return {
        "registered": True,
        "device_id": device_id,
        "device_token": token
    }


@app.post("/api/device/heartbeat")
def heartbeat(
    device_id: str,
    device_token: str
):

    device = devices.get(device_id)

    if not device:
        return {
            "ok": False,
            "message": "Device not registered"
        }

    if device["device_token"] != device_token:
        return {
            "ok": False,
            "message": "Invalid device token"
        }

    device["online"] = True
    device["last_seen"] = datetime.utcnow().isoformat()

    return {
        "ok": True
    }


@app.get("/api/hotspot/config")
def hotspot_config(device_id: str):

    return {
        "device_id": device_id,
        "enabled": True,
        "ssid": "MCOE-Hotspot",
        "password": "MCOE12345678",
        "max_clients": 10
    }


@app.post("/api/hotspot/start")
def hotspot_start(device_id: str):

    device = devices.get(device_id)

    if not device:
        return {
            "success": False,
            "message": "Device not registered"
        }

    device["hotspot"] = True

    return {
        "success": True,
        "device_id": device_id,
        "command": "START_HOTSPOT"
    }


@app.post("/api/hotspot/stop")
def hotspot_stop(device_id: str):

    device = devices.get(device_id)

    if not device:
        return {
            "success": False,
            "message": "Device not registered"
        }

    device["hotspot"] = False

    return {
        "success": True,
        "device_id": device_id,
        "command": "STOP_HOTSPOT"
    }


@app.get("/api/hotspot/status")
def hotspot_status(device_id: str):

    device = devices.get(device_id)

    if not device:
        return {
            "device_id": device_id,
            "hotspot": False,
            "connected_clients": 0,
            "rx_bytes": 0,
            "tx_bytes": 0
        }

    return {
        "device_id": device_id,
        "hotspot": device["hotspot"],
        "connected_clients": device["connected_clients"],
        "rx_bytes": device["rx_bytes"],
        "tx_bytes": device["tx_bytes"]
    }


@app.post("/api/device/usage")
def device_usage(
    device_id: str,
    device_token: str,
    rx_bytes: int = 0,
    tx_bytes: int = 0,
    connected_clients: int = 0
):

    device = devices.get(device_id)

    if not device:
        return {
            "ok": False,
            "message": "Device not registered"
        }

    if device["device_token"] != device_token:
        return {
            "ok": False,
            "message": "Invalid device token"
        }

    device["rx_bytes"] = rx_bytes
    device["tx_bytes"] = tx_bytes
    device["connected_clients"] = connected_clients

    return {
        "ok": True
    }


@app.get("/api/device/status")
def device_status(device_id: str):

    device = devices.get(device_id)

    if not device:
        return {
            "registered": False
        }

    return {
        "registered": True,
        "device_id": device["device_id"],
        "device_name": device["device_name"],
        "online": device["online"],
        "last_seen": device["last_seen"],
        "hotspot": device["hotspot"],
        "connected_clients": device["connected_clients"],
        "rx_bytes": device["rx_bytes"],
        "tx_bytes": device["tx_bytes"]
    }
