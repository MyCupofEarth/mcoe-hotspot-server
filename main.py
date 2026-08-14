from fastapi import FastAPI, HTTPException
from datetime import datetime
import secrets

app = FastAPI(
    title="MCOE eSIM Provisioning Server",
    version="2.0.0"
)

devices = {}
esim_requests = {}


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "name": "MCOE eSIM Server",
        "status": "online",
        "version": "2.0.0"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "server": "MCOE eSIM Server"
    }


# =========================================================
# DEVICE REGISTRATION
# =========================================================

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

        "eid": None,

        "esim_status": "not_provisioned"
    }

    return {

        "registered": True,

        "device_id": device_id,

        "device_token": token
    }


# =========================================================
# DEVICE HEARTBEAT
# =========================================================

@app.post("/api/device/heartbeat")
def heartbeat(
    device_id: str,
    device_token: str
):

    device = devices.get(device_id)

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )

    if device["device_token"] != device_token:

        raise HTTPException(
            status_code=401,
            detail="Invalid device token"
        )

    device["online"] = True

    device["last_seen"] = \
        datetime.utcnow().isoformat()

    return {
        "ok": True
    }


# =========================================================
# eSIM PROVISION REQUEST
# =========================================================

@app.get("/api/esim/provision")
def esim_provision(device_id: str):

    # Android/AOSP TS.48 test profile
    smdp_address = "prod.smdp-plus.rsp.goog"
matching_id = "3TD6-8L82-HUE1-LVN6"

activation_code = (
    "1$prod.smdp-plus.rsp.goog$3TD6-8L82-HUE1-LVN6"
)

    return {
        "provider": "MCOE",
        "device_id": device_id,
        "type": "esim",
        "status": "ready",

        "smdp_address": smdp_address,

        "matching_id": matching_id,

        "activation_code": activation_code,

        "message": "MCOE test eSIM profile ready"
    }


# =========================================================
# eSIM STATUS
# =========================================================

@app.get("/api/esim/status")
def esim_status(
    device_id: str
):

    device = devices.get(device_id)

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )


    return {

        "provider":
            "MCOE",

        "device_id":
            device_id,

        "eid":
            device["eid"],

        "status":
            device["esim_status"],

        "esim_active":
            device["esim_status"] == "active"
    }
