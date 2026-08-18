from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
import secrets
import os
import httpx


# =========================================================
# MCOE eSIM PROVISIONING API
# =========================================================

app = FastAPI(
    title="MCOE eSIM Provisioning API",
    version="5.0.0"
)


# =========================================================
# CONFIGURATION
# =========================================================

SM_DP_PLUS_ADDRESS = os.getenv(
    "SM_DP_PLUS_ADDRESS",
    "mcoe-sm-dp-pysim.onrender.com"
).strip().replace("https://", "").rstrip("/")

SM_DP_PLUS_URL = f"https://{SM_DP_PLUS_ADDRESS}"


# =========================================================
# TEMPORARY STORAGE
# =========================================================

devices = {}
esim_requests = {}


# =========================================================
# AUTHORIZED TEST PROFILES
# =========================================================
#
# These filenames MUST correspond to files that actually
# exist in:
#
# smdpp-data/upp/
#
# We only select from the profiles you uploaded.
#

test_profiles = {

    "TS48V1-A-UNIQUE": {
        "profile_name": "TS48 V1 A UNIQUE",
        "filename": "TS48V1-A-UNIQUE.der",
        "status": "available"
    },

    "TS48V1-B-UNIQUE": {
        "profile_name": "TS48 V1 B UNIQUE",
        "filename": "TS48V1-B-UNIQUE.der",
        "status": "available"
    },

    "TS48V2-SAIP2-1-BERTLV-UNIQUE": {
        "profile_name": "TS48 V2 SAIP2.1 BERTLV UNIQUE",
        "filename": "TS48V2-SAIP2-1-BERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V2-SAIP2-1-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V2 SAIP2.1 NoBERTLV UNIQUE",
        "filename": "TS48V2-SAIP2-1-NOBERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V2-SAIP2-3-BERTLV-UNIQUE": {
        "profile_name": "TS48 V2 SAIP2.3 BERTLV UNIQUE",
        "filename": "TS48V2-SAIP2-3-BERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V2-SAIP2-3-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V2 SAIP2.3 NoBERTLV UNIQUE",
        "filename": "TS48V2-SAIP2-3-NOBERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V3-SAIP2-1-BERTLV-UNIQUE": {
        "profile_name": "TS48 V3 SAIP2.1 BERTLV UNIQUE",
        "filename": "TS48V3-SAIP2-1-BERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V3-SAIP2-1-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V3 SAIP2.1 NoBERTLV UNIQUE",
        "filename": "TS48V3-SAIP2-1-NOBERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V3-SAIP2-3-BERTLV-UNIQUE": {
        "profile_name": "TS48 V3 SAIP2.3 BERTLV UNIQUE",
        "filename": "TS48V3-SAIP2-3-BERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V3-SAIP2-3-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V3 SAIP2.3 NoBERTLV UNIQUE",
        "filename": "TS48V3-SAIP2-3-NOBERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V4-SAIP2-1A-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V4 SAIP2.1A NoBERTLV UNIQUE",
        "filename": "TS48V4-SAIP2-1A-NOBERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V4-SAIP2-1B-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V4 SAIP2.1B NoBERTLV UNIQUE",
        "filename": "TS48V4-SAIP2-1B-NOBERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V4-SAIP2-3-BERTLV-UNIQUE": {
        "profile_name": "TS48 V4 SAIP2.3 BERTLV UNIQUE",
        "filename": "TS48V4-SAIP2-3-BERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V4-SAIP2-3-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V4 SAIP2.3 NoBERTLV UNIQUE",
        "filename": "TS48V4-SAIP2-3-NOBERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V5-SAIP2-1A-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V5 SAIP2.1A NoBERTLV UNIQUE",
        "filename": "TS48V5-SAIP2-1A-NOBERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V5-SAIP2-1B-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V5 SAIP2.1B NoBERTLV UNIQUE",
        "filename": "TS48V5-SAIP2-1B-NOBERTLV-UNIQUE.der",
        "status": "available"
    },

    "TS48V5-SAIP2-3-BERTLV-SUCI-UNIQUE": {
        "profile_name": "TS48 V5 SAIP2.3 BERTLV SUCI UNIQUE",
        "filename": "TS48V5-SAIP2-3-BERTLV-SUCI-UNIQUE.der",
        "status": "available"
    },

    "TS48V5-SAIP2-3-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V5 SAIP2.3 NoBERTLV UNIQUE",
        "filename": "TS48V5-SAIP2-3-NOBERTLV-UNIQUE.der",
        "status": "available"
    }
}


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


class ProvisionRequest(BaseModel):
    device_id: str


class CancelProvisionRequest(BaseModel):
    device_id: str


# =========================================================
# HELPERS
# =========================================================

def utc_now():
    return datetime.now(timezone.utc).isoformat()


def generate_device_token():
    return secrets.token_urlsafe(32)


def generate_request_id():
    return "MCOE-" + secrets.token_hex(16).upper()


async def check_smdp():
    """
    Check whether the separate pySim SM-DP+ service is reachable.
    """

    try:

        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:

            response = await client.get(
                f"{SM_DP_PLUS_URL}/"
            )

            return {
                "reachable": True,
                "http_status": response.status_code
            }

    except Exception as e:

        return {
            "reachable": False,
            "error": str(e)
        }


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {

        "name":
            "MCOE eSIM Provisioning API",

        "status":
            "online",

        "version":
            "5.0.0",

        "service":
            "MCOE API",

        "smdp_plus":
            SM_DP_PLUS_URL
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
async def health():

    smdp = await check_smdp()

    return {

        "status":
            "healthy",

        "server":
            "MCOE eSIM Provisioning API",

        "timestamp":
            utc_now(),

        "smdp_plus":
            SM_DP_PLUS_URL,

        "smdp_plus_reachable":
            smdp["reachable"],

        "smdp_plus_http_status":
            smdp.get("http_status")
    }


# =========================================================
# SM-DP+ CONNECTION TEST
# =========================================================

@app.get("/api/esim/smdp")
async def smdp_configuration():

    smdp = await check_smdp()

    return {

        "provider":
            "MCOE",

        "smdp_address":
            SM_DP_PLUS_ADDRESS,

        "smdp_url":
            SM_DP_PLUS_URL,

        "protocol":
            "GSMA RSP / ES9+",

        "reachable":
            smdp["reachable"],

        "http_status":
            smdp.get("http_status"),

        "status":
            "configured"
            if smdp["reachable"]
            else "unreachable"
    }


# =========================================================
# DEVICE REGISTRATION
# =========================================================

@app.post("/api/device/register")
def register_device(
    request: DeviceRegisterRequest
):

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

    existing = devices.get(device_id)

    if existing:

        existing["device_name"] = device_name
        existing["online"] = True
        existing["last_seen"] = utc_now()

        return {
            "registered": True,
            "existing": True,
            "device_id": device_id,
            "device_token": existing["device_token"],
            "eid": existing["eid"],
            "esim_status": existing["esim_status"]
        }

    token = generate_device_token()
    now = utc_now()

    devices[device_id] = {

        "device_id":
            device_id,

        "device_name":
            device_name,

        "device_token":
            token,

        "online":
            True,

        "registered_at":
            now,

        "last_seen":
            now,

        "eid":
            None,

        "esim_status":
            "not_provisioned",

        "active_request_id":
            None
    }

    return {

        "registered":
            True,

        "existing":
            False,

        "device_id":
            device_id,

        "device_token":
            token,

        "eid":
            None,

        "esim_status":
            "not_provisioned"
    }


# =========================================================
# HEARTBEAT
# =========================================================

@app.post("/api/device/heartbeat")
def heartbeat(
    request: DeviceHeartbeatRequest
):

    device = devices.get(
        request.device_id
    )

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

        "ok":
            True,

        "device_id":
            request.device_id,

        "online":
            True,

        "last_seen":
            device["last_seen"]
    }


# =========================================================
# DEVICE STATUS
# =========================================================

@app.get("/api/device/status")
def device_status(
    device_id: str
):

    device = devices.get(device_id)

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )

    return device


# =========================================================
# UPDATE EID
# =========================================================

@app.post("/api/device/eid")
def update_eid(
    request: EIDRequest
):

    device = devices.get(
        request.device_id
    )

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )

    eid = request.eid.strip()

    if len(eid) != 32 or not eid.isdigit():

        raise HTTPException(
            status_code=400,
            detail="Invalid EID. Expected 32 digits."
        )

    device["eid"] = eid

    return {

        "ok":
            True,

        "device_id":
            request.device_id,

        "eid":
            eid,

        "esim_status":
            device["esim_status"]
    }


# =========================================================
# TEST PROFILE LIST
# =========================================================

@app.get("/api/esim/profiles")
def list_profiles():

    profiles = []

    for matching_id, profile in test_profiles.items():

        profiles.append({

            "matching_id":
                matching_id,

            "profile_name":
                profile["profile_name"],

            "filename":
                profile["filename"],

            "status":
                profile["status"]
        })

    return {

        "provider":
            "MCOE",

        "smdp_address":
            SM_DP_PLUS_ADDRESS,

        "count":
            len(profiles),

        "profiles":
            profiles
    }


# =========================================================
# PROVISION
# =========================================================

@app.post("/api/esim/provision")
def request_esim_provision(
    request: ProvisionRequest
):

    device_id = request.device_id.strip()

    device = devices.get(device_id)

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )

    if not device["eid"]:

        raise HTTPException(
            status_code=400,
            detail="Device EID has not been registered"
        )

    # -----------------------------------------------------
    # EXISTING REQUEST
    # -----------------------------------------------------

    active_id = device.get(
        "active_request_id"
    )

    if active_id:

        existing = esim_requests.get(
            active_id
        )

        if existing and existing["status"] in (
            "pending",
            "provisioning"
        ):

            return {

                "provider":
                    "MCOE",

                "request_id":
                    active_id,

                "device_id":
                    device_id,

                "eid":
                    device["eid"],

                "status":
                    existing["status"],

                "smdp_address":
                    SM_DP_PLUS_ADDRESS,

                "matching_id":
                    existing["matching_id"],

                "message":
                    "Existing provisioning request"
            }

    # -----------------------------------------------------
    # TEST PROFILE
    # -----------------------------------------------------

    profile = None
    matching_id = None

    for mid, candidate in test_profiles.items():

        if candidate["status"] == "available":

            matching_id = mid
            profile = candidate

            break

    if not profile:

        raise HTTPException(
            status_code=503,
            detail="No authorized test profile available"
        )

    # -----------------------------------------------------
    # CREATE REQUEST
    # -----------------------------------------------------

    request_id = generate_request_id()
    now = utc_now()

    esim_requests[request_id] = {

        "request_id":
            request_id,

        "device_id":
            device_id,

        "eid":
            device["eid"],

        "matching_id":
            matching_id,

        "profile_name":
            profile["profile_name"],

        "profile_file":
            profile["filename"],

        "smdp_address":
            SM_DP_PLUS_ADDRESS,

        "smdp_url":
            SM_DP_PLUS_URL,

        "status":
            "pending",

        "created_at":
            now,

        "updated_at":
            now
    }

    profile["status"] = "reserved"

    device["esim_status"] = "provisioning"
    device["active_request_id"] = request_id

    return {

        "provider":
            "MCOE",

        "request_id":
            request_id,

        "device_id":
            device_id,

        "eid":
            device["eid"],

        "status":
            "pending",

        "smdp_address":
            SM_DP_PLUS_ADDRESS,

        "smdp_url":
            SM_DP_PLUS_URL,

        "matching_id":
            matching_id,

        "profile":
            profile["profile_name"],

        "message":
            "Authorized test profile reserved. The eUICC/LPA must now perform the GSMA RSP download."
    }


# =========================================================
# REQUEST STATUS
# =========================================================

@app.get("/api/esim/request")
def esim_request_status(
    request_id: str
):

    request = esim_requests.get(
        request_id
    )

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

        "active_request_id":
            device["active_request_id"],

        "esim_active":
            device["esim_status"] == "active",

        "smdp_address":
            SM_DP_PLUS_ADDRESS
    }


# =========================================================
# CANCEL PROVISIONING
# =========================================================

@app.post("/api/esim/cancel")
def cancel_esim_provision(
    request: CancelProvisionRequest
):

    device = devices.get(
        request.device_id
    )

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )

    request_id = device.get(
        "active_request_id"
    )

    if not request_id:

        return {
            "ok": True,
            "message": "No active provisioning request"
        }

    esim_request = esim_requests.get(
        request_id
    )

    if esim_request:

        matching_id = esim_request[
            "matching_id"
        ]

        profile = test_profiles.get(
            matching_id
        )

        if profile:

            profile["status"] = "available"

        esim_request["status"] = "cancelled"
        esim_request["updated_at"] = utc_now()

    device["active_request_id"] = None
    device["esim_status"] = "not_provisioned"

    return {

        "ok":
            True,

        "request_id":
            request_id,

        "device_id":
            request.device_id,

        "status":
            "cancelled"
    }


# =========================================================
# ADMIN / DEVELOPMENT
# =========================================================

@app.get("/api/devices")
def list_devices():

    return {

        "count":
            len(devices),

        "devices":
            list(devices.values())
    }


@app.get("/api/esim/requests")
def list_esim_requests():

    return {

        "count":
            len(esim_requests),

        "requests":
            list(esim_requests.values())
    }


# =========================================================
# RELEASE TEST PROFILE
# =========================================================

@app.post("/api/esim/profile/{matching_id}/release")
def release_profile(
    matching_id: str
):

    profile = test_profiles.get(
        matching_id
    )

    if not profile:

        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )

    profile["status"] = "available"

    return {

        "ok":
            True,

        "matching_id":
            matching_id,

        "status":
            "available"
    }
