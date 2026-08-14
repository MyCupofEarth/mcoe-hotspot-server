from fastapi import FastAPI
from datetime import datetime
import secrets


app = FastAPI(
    title="MCOE Server",
    version="1.0.0"
)


# --------------------------------------------------
# IN-MEMORY DEVICE DATABASE
# --------------------------------------------------

devices = {}


# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "name": "MCOE Server",
        "status": "online",
        "version": "1.0.0"
    }


# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "server": "MCOE Server"
    }


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.post("/api/login")
def login(
    username: str,
    password: str
):

    if username == "mcoe" and password == "mcoe":

        return {
            "success": True,
            "access_token": secrets.token_urlsafe(32)
        }

    return {
        "success": False,
        "message": "Invalid username or password"
    }


# --------------------------------------------------
# DEVICE REGISTER
# --------------------------------------------------

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

        "last_seen":
            datetime.utcnow().isoformat(),

        "hotspot": False,

        "connected_clients": 0,

        "rx_bytes": 0,

        "tx_bytes": 0,

        "esim": False
    }

    return {

        "registered": True,

        "device_id": device_id,

        "device_token": token
    }


# --------------------------------------------------
# DEVICE HEARTBEAT
# --------------------------------------------------

@app.post("/api/device/heartbeat")
def heartbeat(
    device_id: str,
    device_token: str
):

    device = devices.get(device_id)

    if not device:

        return {

            "ok": False,

            "message":
                "Device not registered"
        }

    if (
        device["device_token"]
        != device_token
    ):

        return {

            "ok": False,

            "message":
                "Invalid device token"
        }

    device["online"] = True

    device["last_seen"] = (
        datetime.utcnow().isoformat()
    )

    return {
        "ok": True
    }


# ==================================================
# ESIM PROVISIONING
# ==================================================

@app.get("/api/esim/provision")
def esim_provision(device_id: str):

    device = devices.get(device_id)

    if not device:

        return {
            "provider": "MCOE",
            "device_id": device_id,
            "type": "esim",
            "status": "device_not_registered",
            "message": "Register device first"
        }

    return {
        "provider": "MCOE",
        "device_id": device_id,
        "type": "esim",
        "status": "pending",
        "message": "eSIM provisioning request received"
    }


# ==================================================
# ESIM STATUS
# ==================================================

@app.get("/api/esim/status")
def esim_status(
    device_id: str
):

    device = devices.get(device_id)

    if not device:

        return {

            "device_id": device_id,

            "registered": False,

            "esim": False
        }

    return {

        "device_id": device_id,

        "registered": True,

        "esim":
            device["esim"]
    }


# ==================================================
# HOTSPOT CONFIGURATION
# ==================================================

@app.get("/api/hotspot/config")
def hotspot_config(
    device_id: str
):

    return {

        "name": "MCOE",

        "version": 1,

        "hotspot": {

            "ssid":
                "MCOE-Hotspot",

            "password":
                "MCOE12345678",

            "max_clients":
                10
        }
    }


# ==================================================
# HOTSPOT START
# ==================================================

@app.post("/api/hotspot/start")
def hotspot_start(
    device_id: str
):

    device = devices.get(device_id)

    if not device:

        return {

            "success": False,

            "message":
                "Device not registered"
        }

    device["hotspot"] = True

    return {

        "success": True,

        "device_id":
            device_id,

        "command":
            "START_HOTSPOT"
    }


# ==================================================
# HOTSPOT STOP
# ==================================================

@app.post("/api/hotspot/stop")
def hotspot_stop(
    device_id: str
):

    device = devices.get(device_id)

    if not device:

        return {

            "success": False,

            "message":
                "Device not registered"
        }

    device["hotspot"] = False

    return {

        "success": True,

        "device_id":
            device_id,

        "command":
            "STOP_HOTSPOT"
    }


# ==================================================
# HOTSPOT STATUS
# ==================================================

@app.get("/api/hotspot/status")
def hotspot_status(
    device_id: str
):

    device = devices.get(device_id)

    if not device:

        return {

            "device_id":
                device_id,

            "hotspot":
                False,

            "connected_clients":
                0,

            "rx_bytes":
                0,

            "tx_bytes":
                0
        }

    return {

        "device_id":
            device_id,

        "hotspot":
            device["hotspot"],

        "connected_clients":
            device["connected_clients"],

        "rx_bytes":
            device["rx_bytes"],

        "tx_bytes":
            device["tx_bytes"]
    }


# ==================================================
# DEVICE USAGE
# ==================================================

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

            "message":
                "Device not registered"
        }

    if (
        device["device_token"]
        != device_token
    ):

        return {

            "ok": False,

            "message":
                "Invalid device token"
        }

    device["rx_bytes"] = rx_bytes

    device["tx_bytes"] = tx_bytes

    device["connected_clients"] = (
        connected_clients
    )

    return {
        "ok": True
    }


# ==================================================
# DEVICE STATUS
# ==================================================

@app.get("/api/device/status")
def device_status(
    device_id: str
):

    device = devices.get(device_id)

    if not device:

        return {
            "registered": False
        }

    return {

        "registered": True,

        "device_id":
            device["device_id"],

        "device_name":
            device["device_name"],

        "online":
            device["online"],

        "last_seen":
            device["last_seen"],

        "hotspot":
            device["hotspot"],

        "connected_clients":
            device["connected_clients"],

        "rx_bytes":
            device["rx_bytes"],

        "tx_bytes":
            device["tx_bytes"],

        "esim":
            device["esim"]
    }
