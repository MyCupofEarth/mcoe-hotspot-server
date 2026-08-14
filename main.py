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

@app.post("/api/esim/provision")
def esim_provision(
    device_id: str,
    eid: str | None = None
):

    device = devices.get(device_id)

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )


    # Save EID if supplied
    if eid:

        device["eid"] = eid


    request_id = secrets.token_urlsafe(24)


    esim_requests[request_id] = {

        "request_id":
            request_id,

        "device_id":
            device_id,

        "eid":
            eid,

        "status":
            "pending",

        "created_at":
            datetime.utcnow().isoformat()
    }


    device["esim_status"] = "pending"


    return {

        "provider":
            "MCOE",

        "device_id":
            device_id,

        "request_id":
            request_id,

        "type":
            "esim",

        "status":
            "pending",

        "message":
            "eSIM provisioning request received"
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
