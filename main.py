from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
import secrets


# =========================================================
# MCOE eSIM API SERVER
# =========================================================

app = FastAPI(
    title="MCOE eSIM Provisioning API",
    version="3.0.0"
)


# =========================================================
# TEMPORARY IN-MEMORY STORAGE
# =========================================================
#
# IMPORTANT:
# Render can restart your service.
# These dictionaries are therefore temporary.
#
# Later we can replace them with PostgreSQL.
#

devices = {}
esim_requests = {}


# =========================================================
# REQUEST MODELS
# =========================================================

class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_name: str


class DeviceHeartbeatRequest(BaseModel):
    device_id: str
    device_token: str


class EIDRequest(BaseModel):
    device_id: str
    eid: str


# =========================================================
# HELPERS
# =========================================================

def utc_now():
    return datetime.now(timezone.utc).isoformat()


def generate_device_token():
    return secrets.token_urlsafe(32)


def generate_request_id():
    return "MCOE-" + secrets.token_hex(16).upper()


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "name": "MCOE eSIM Provisioning API",
        "status": "online",
        "version": "3.0.0",
        "service": "MCOE API"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "server": "MCOE eSIM Provisioning API",
        "timestamp": utc_now()
    }


# =========================================================
# DEVICE REGISTRATION
# =========================================================

@app.post("/api/device/register")
def register_device(request: DeviceRegisterRequest):

    device_id = request.device_id.strip()
    device_name = request.device_name.strip()

    if not device_id:
        raise HTTPException(
            status_code=400,
            detail="device_id is required"
        )

    if not device_name:
        raise HTTPException(
            status_code=400,
            detail="device_name is required"
        )

    # -----------------------------------------------------
    # Existing device
    # -----------------------------------------------------

    existing_device = devices.get(device_id)

    if existing_device:

        existing_device["device_name"] = device_name
        existing_device["online"] = True
        existing_device["last_seen"] = utc_now()

        return {
            "registered": True,
            "existing": True,
            "device_id": device_id,
            "device_token": existing_device["device_token"],
            "eid": existing_device["eid"],
            "esim_status": existing_device["esim_status"]
        }

    # -----------------------------------------------------
    # New device
    # -----------------------------------------------------

    device_token = generate_device_token()

    devices[device_id] = {

        "device_id": device_id,

        "device_name": device_name,

        "device_token": device_token,

        "online": True,

        "registered_at": utc_now(),

        "last_seen": utc_now(),

        "eid": None,

        "esim_status": "not_provisioned"
    }

    return {

        "registered": True,

        "existing": False,

        "device_id": device_id,

        "device_token": device_token,

        "eid": None,

        "esim_status": "not_provisioned"
    }


# =========================================================
# DEVICE HEARTBEAT
# =========================================================

@app.post("/api/device/heartbeat")
def heartbeat(request: DeviceHeartbeatRequest):

    device = devices.get(request.device_id)

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )

    if device["device_token"] != request.device_token:

        raise HTTPException(
            status_code=401,
            detail="Invalid device token"
        )

    device["online"] = True
    device["last_seen"] = utc_now()

    return {

        "ok": True,

        "device_id": request.device_id,

        "online": True,

        "last_seen": device["last_seen"]
    }


# =========================================================
# DEVICE STATUS
# =========================================================

@app.get("/api/device/status")
def device_status(device_id: str):

    device = devices.get(device_id)

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )

    return {

        "device_id": device["device_id"],

        "device_name": device["device_name"],

        "online": device["online"],

        "registered_at": device["registered_at"],

        "last_seen": device["last_seen"],

        "eid": device["eid"],

        "esim_status": device["esim_status"]
    }


# =========================================================
# UPDATE DEVICE EID
# =========================================================

@app.post("/api/device/eid")
def update_eid(request: EIDRequest):

    device = devices.get(request.device_id)

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )

    eid = request.eid.strip()

    if not eid:

        raise HTTPException(
            status_code=400,
            detail="EID is required"
        )

    device["eid"] = eid

    return {

        "ok": True,

        "device_id": request.device_id,

        "eid": eid,

        "esim_status": device["esim_status"]
    }


# =========================================================
# eSIM PROVISION REQUEST
# =========================================================
#
# This creates an MCOE provisioning request.
#
# IMPORTANT:
# This does NOT directly install an eSIM.
#
# The actual eSIM profile download must be handled by
# the authorized SM-DP+ / RSP environment.
#

@app.post("/api/esim/provision")
def request_esim_provision(device_id: str):

    device = devices.get(device_id)

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )

    request_id = generate_request_id()

    esim_requests[request_id] = {

        "request_id": request_id,

        "device_id": device_id,

        "eid": device["eid"],

        "status": "pending",

        "created_at": utc_now(),

        "updated_at": utc_now()
    }

    device["esim_status"] = "provisioning"

    return {

        "provider": "MCOE",

        "request_id": request_id,

        "device_id": device_id,

        "eid": device["eid"],

        "type": "esim",

        "status": "pending",

        "message": "MCOE eSIM provisioning request created"
    }


# =========================================================
# eSIM REQUEST STATUS
# =========================================================

@app.get("/api/esim/request")
def esim_request_status(request_id: str):

    request = esim_requests.get(request_id)

    if not request:

        raise HTTPException(
            status_code=404,
            detail="eSIM request not found"
        )

    return request


# =========================================================
# eSIM STATUS
# =========================================================

@app.get("/api/esim/status")
def esim_status(device_id: str):

    device = devices.get(device_id)

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )

    return {

        "provider": "MCOE",

        "device_id": device_id,

        "eid": device["eid"],

        "status": device["esim_status"],

        "esim_active":
            device["esim_status"] == "active"
    }


# =========================================================
# ADMIN / DEBUG DEVICE LIST
# =========================================================
#
# Useful during development.
# Do NOT expose this publicly in production without
# authentication.
#

@app.get("/api/devices")
def list_devices():

    return {

        "count": len(devices),

        "devices": list(devices.values())
    }


# =========================================================
# ADMIN / DEBUG eSIM REQUEST LIST
# =========================================================
#
# Development only.
#

@app.get("/api/esim/requests")
def list_esim_requests():

    return {

        "count": len(esim_requests),

        "requests": list(esim_requests.values())
    }
