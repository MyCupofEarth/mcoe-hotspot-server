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
    version="8.0.0"
)


# =========================================================
# CONFIGURATION
# =========================================================

SM_DP_PLUS_ADDRESS = os.getenv(
    "SM_DP_PLUS_ADDRESS",
    "mcoe-sm-dp-pysim.onrender.com"
).strip()

SM_DP_PLUS_ADDRESS = (
    SM_DP_PLUS_ADDRESS
    .replace("https://", "")
    .replace("http://", "")
    .rstrip("/")
)

SM_DP_PLUS_URL = f"https://{SM_DP_PLUS_ADDRESS}"


# =========================================================
# TEMPORARY STORAGE
# =========================================================

devices = {}

esim_requests = {}


# =========================================================
# PYSim TEST PROFILES
# =========================================================

test_profiles = {

    "TS48V1-A-UNIQUE": {
        "profile_name": "TS48 V1 A UNIQUE",
        "filename": "TS48V1-A-UNIQUE.der",
        "status": "available",
    },

    "TS48V1-B-UNIQUE": {
        "profile_name": "TS48 V1 B UNIQUE",
        "filename": "TS48V1-B-UNIQUE.der",
        "status": "available",
    },

    "TS48V2-SAIP2-1-BERTLV-UNIQUE": {
        "profile_name": "TS48 V2 SAIP2.1 BERTLV UNIQUE",
        "filename": "TS48V2-SAIP2-1-BERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V2-SAIP2-1-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V2 SAIP2.1 NoBERTLV UNIQUE",
        "filename": "TS48V2-SAIP2-1-NOBERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V2-SAIP2-3-BERTLV-UNIQUE": {
        "profile_name": "TS48 V2 SAIP2.3 BERTLV UNIQUE",
        "filename": "TS48V2-SAIP2-3-BERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V2-SAIP2-3-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V2 SAIP2.3 NoBERTLV UNIQUE",
        "filename": "TS48V2-SAIP2-3-NOBERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V3-SAIP2-1-BERTLV-UNIQUE": {
        "profile_name": "TS48 V3 SAIP2.1 BERTLV UNIQUE",
        "filename": "TS48V3-SAIP2-1-BERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V3-SAIP2-1-NOBERTLV-UNIQUE": {
        "profile_name": "TS48V3-SAIP2.1 NoBERTLV UNIQUE",
        "filename": "TS48V3-SAIP2-1-NOBERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V3-SAIP2-3-BERTLV-UNIQUE": {
        "profile_name": "TS48 V3 SAIP2.3 BERTLV UNIQUE",
        "filename": "TS48V3-SAIP2-3-BERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V3-SAIP2-3-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V3 SAIP2.3 NoBERTLV UNIQUE",
        "filename": "TS48V3-SAIP2-3-NOBERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V4-SAIP2-1A-NOBERTLV-UNIQUE": {
        "profile_name": "TS48 V4 SAIP2.1A NoBERTLV UNIQUE",
        "filename": "TS48V4-SAIP2-1A-NOBERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V4-SAIP2-1B-NOBERTLV-UNIQUE": {
        "profile_name": "TS48V4-SAIP2.1B NoBERTLV UNIQUE",
        "filename": "TS48V4-SAIP2-1B-NOBERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V4-SAIP2-3-BERTLV-UNIQUE": {
        "profile_name": "TS48V4-SAIP2.3 BERTLV UNIQUE",
        "filename": "TS48V4-SAIP2-3-BERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V4-SAIP2-3-NOBERTLV-UNIQUE": {
        "profile_name": "TS48V4-SAIP2.3 NoBERTLV UNIQUE",
        "filename": "TS48V4-SAIP2-3-NOBERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V5-SAIP2-1A-NOBERTLV-UNIQUE": {
        "profile_name": "TS48V5-SAIP2.1A NoBERTLV UNIQUE",
        "filename": "TS48V5-SAIP2-1A-NOBERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V5-SAIP2-1B-NOBERTLV-UNIQUE": {
        "profile_name": "TS48V5-SAIP2.1B NoBERTLV UNIQUE",
        "filename": "TS48V5-SAIP2-1B-NOBERTLV-UNIQUE.der",
        "status": "available",
    },

    "TS48V5-SAIP2-3-BERTLV-SUCI-UNIQUE": {
        "profile_name": "TS48V5-SAIP2.3 BERTLV SUCI UNIQUE",
        "filename": "TS48V5-SAIP2-3-BERTLV-SUCI-UNIQUE.der",
        "status": "available",
    },

    "TS48V5-SAIP2-3-NOBERTLV-UNIQUE": {
        "profile_name": "TS48V5-SAIP2.3 NoBERTLV UNIQUE",
        "filename": "TS48V5-SAIP2-3-NOBERTLV-UNIQUE.der",
        "status": "available",
    },
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


class ProvisionCompleteRequest(BaseModel):
    device_id: str
    request_id: str
    success: bool


# =========================================================
# HELPERS
# =========================================================

def utc_now():
    return datetime.now(timezone.utc).isoformat()


def generate_device_token():
    return secrets.token_urlsafe(32)


def generate_request_id():
    return "MCOE-" + secrets.token_hex(16).upper()


def find_available_profile():

    for matching_id, profile in test_profiles.items():

        if profile["status"] == "available":

            return matching_id, profile

    return None, None


# =========================================================
# ACTIVATION CODE
# =========================================================
#
# IMPORTANT:
#
# This is the GSMA activation-code container format.
#
# The SM-DP+ must actually recognize the matching ID.
#
# Do NOT substitute the .der filename here.
#
# =========================================================

def build_activation_code(matching_id: str) -> str:

    return (
        f"1${SM_DP_PLUS_ADDRESS}${matching_id}"
    )


# =========================================================
# CHECK SM-DP+
# =========================================================

async def check_smdp():

    try:

        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True
        ) as client:

            response = await client.get(
                SM_DP_PLUS_URL + "/"
            )

            return {

                "reachable":
                    response.status_code < 500,

                "http_status":
                    response.status_code,

                "endpoint":
                    SM_DP_PLUS_URL
            }

    except httpx.RequestError as exc:

        return {

            "reachable":
                False,

            "error":
                str(exc),

            "endpoint":
                SM_DP_PLUS_URL
        }

    except Exception as exc:

        return {

            "reachable":
                False,

            "error":
                str(exc),

            "endpoint":
                SM_DP_PLUS_URL
        }


# =========================================================
# ROOT
# =========================================================

@app.get("/")
async def root():

    smdp = await check_smdp()

    return {

        "name":
            "MCOE eSIM Provisioning API",

        "status":
            "online",

        "version":
            "8.0.0",

        "service":
            "MCOE Control API",

        "smdp_plus":
            SM_DP_PLUS_URL,

        "smdp_plus_reachable":
            smdp["reachable"],

        "smdp_plus_http_status":
            smdp.get("http_status"),

        "profile_count":
            len(test_profiles)
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

        "version":
            "8.0.0",

        "timestamp":
            utc_now(),

        "smdp_plus":
            SM_DP_PLUS_URL,

        "smdp_plus_reachable":
            smdp["reachable"],

        "smdp_plus_http_status":
            smdp.get("http_status"),

        "devices":
            len(devices),

        "requests":
            len(esim_requests),

        "profiles":
            len(test_profiles)
    }


# =========================================================
# SM-DP+ CONFIGURATION
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
            "reachable"
            if smdp["reachable"]
            else "unreachable",

        "note":
            (
                "A 404 from the web root does not prove "
                "that the ES9+ endpoint is unavailable."
            )
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

            "registered":
                True,

            "existing":
                True,

            "device_id":
                device_id,

            "device_token":
                existing["device_token"],

            "eid":
                existing["eid"],

            "eid_status":
                (
                    "registered"
                    if existing["eid"]
                    else "protected_or_unavailable"
                ),

            "esim_status":
                existing["esim_status"]
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

        "eid_status":
            "protected_or_unavailable",

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

        "eid_status":
            "protected_or_unavailable",

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

    return {

        "device_id":
            device["device_id"],

        "device_name":
            device["device_name"],

        "online":
            device["online"],

        "registered_at":
            device["registered_at"],

        "last_seen":
            device["last_seen"],

        "eid":
            device["eid"],

        "eid_status":
            device.get(
                "eid_status",
                "protected_or_unavailable"
            ),

        "esim_status":
            device["esim_status"],

        "active_request_id":
            device["active_request_id"]
    }


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

    if (
        len(eid) != 32
        or not eid.isdigit()
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid EID. Expected 32 digits."
        )

    device["eid"] = eid
    device["eid_status"] = "registered"

    return {

        "ok":
            True,

        "device_id":
            request.device_id,

        "eid":
            eid,

        "eid_status":
            "registered",

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

    # -----------------------------------------------------
    # DEVICE MUST EXIST
    # -----------------------------------------------------

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )

    # -----------------------------------------------------
    # EID IS OPTIONAL
    # -----------------------------------------------------
    #
    # Android may expose the eUICC hardware but protect
    # the EID from a normal application.
    #
    # Therefore:
    #
    # eid == None
    #
    # does NOT stop activation-code provisioning.
    #
    # -----------------------------------------------------

    eid = device.get("eid")

    if eid:

        device["eid_status"] = "registered"

    else:

        device["eid_status"] = "protected_or_unavailable"


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
                    device.get("eid"),

                "eid_status":
                    device.get(
                        "eid_status",
                        "protected_or_unavailable"
                    ),

                "status":
                    existing["status"],

                "smdp_address":
                    SM_DP_PLUS_ADDRESS,

                "smdp_url":
                    SM_DP_PLUS_URL,

                "matching_id":
                    existing["matching_id"],

                "activation_code":
                    existing["activation_code"],

                "profile":
                    existing["profile_name"],

                "profile_file":
                    existing["profile_file"],

                "message":
                    "Existing provisioning request."
            }


    # -----------------------------------------------------
    # FIND PROFILE
    # -----------------------------------------------------

    matching_id, profile = find_available_profile()

    if not profile:

        raise HTTPException(
            status_code=503,
            detail=(
                "No test profile is currently available."
            )
        )


    # -----------------------------------------------------
    # BUILD ACTIVATION CODE
    # -----------------------------------------------------

    activation_code = build_activation_code(
        matching_id
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
            eid,

        "eid_status":
            device.get(
                "eid_status",
                "protected_or_unavailable"
            ),

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

        "activation_code":
            activation_code,

        "status":
            "pending",

        "created_at":
            now,

        "updated_at":
            now
    }


    # -----------------------------------------------------
    # RESERVE PROFILE
    # -----------------------------------------------------

    profile["status"] = "reserved"

    device["esim_status"] = "provisioning"

    device["active_request_id"] = request_id


    # -----------------------------------------------------
    # RETURN PROVISIONING INFORMATION
    # -----------------------------------------------------

    return {

        "provider":
            "MCOE",

        "request_id":
            request_id,

        "device_id":
            device_id,

        "eid":
            eid,

        "eid_status":
            device.get(
                "eid_status",
                "protected_or_unavailable"
            ),

        "status":
            "pending",

        "smdp_address":
            SM_DP_PLUS_ADDRESS,

        "smdp_url":
            SM_DP_PLUS_URL,

        "matching_id":
            matching_id,

        "activation_code":
            activation_code,

        "profile":
            profile["profile_name"],

        "profile_file":
            profile["filename"],

        "message":
            (
                "Test profile reserved. "
                "The authorized Android LPA/eUICC "
                "will perform the RSP download."
            )
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

    return {

        "request_id":
            request["request_id"],

        "device_id":
            request["device_id"],

        "eid":
            request["eid"],

        "eid_status":
            request.get(
                "eid_status",
                "protected_or_unavailable"
            ),

        "matching_id":
            request["matching_id"],

        "profile_name":
            request["profile_name"],

        "profile_file":
            request["profile_file"],

        "smdp_address":
            request["smdp_address"],

        "smdp_url":
            request["smdp_url"],

        "activation_code":
            request["activation_code"],

        "status":
            request["status"],

        "created_at":
            request["created_at"],

        "updated_at":
            request["updated_at"]
    }


# =========================================================
# COMPLETE PROVISIONING
# =========================================================

@app.post("/api/esim/complete")
def complete_provisioning(
    request: ProvisionCompleteRequest
):

    device = devices.get(
        request.device_id
    )

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )

    esim_request = esim_requests.get(
        request.request_id
    )

    if not esim_request:

        raise HTTPException(
            status_code=404,
            detail="eSIM request not found"
        )

    if esim_request["device_id"] != request.device_id:

        raise HTTPException(
            status_code=403,
            detail="Request does not belong to device"
        )

    matching_id = esim_request["matching_id"]

    profile = test_profiles.get(
        matching_id
    )


    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    if request.success:

        esim_request["status"] = "active"
        esim_request["updated_at"] = utc_now()

        device["esim_status"] = "active"
        device["active_request_id"] = request.request_id

        if profile:

            profile["status"] = "active"

        return {

            "ok":
                True,

            "device_id":
                request.device_id,

            "request_id":
                request.request_id,

            "status":
                "active",

            "message":
                "eSIM provisioning marked complete."
        }


    # -----------------------------------------------------
    # FAILURE
    # -----------------------------------------------------

    esim_request["status"] = "failed"
    esim_request["updated_at"] = utc_now()

    device["esim_status"] = "not_provisioned"
    device["active_request_id"] = None

    if profile:

        profile["status"] = "available"

    return {

        "ok":
            False,

        "device_id":
            request.device_id,

        "request_id":
            request.request_id,

        "status":
            "failed",

        "message":
            "eSIM provisioning marked failed."
    }


# =========================================================
# eSIM STATUS
# =========================================================

@app.get("/api/esim/status")
def esim_status(
    device_id: str
):

    device = devices.get(
        device_id
    )

    if not device:

        raise HTTPException(
            status_code=404,
            detail="Device not registered"
        )

    active_request = None

    active_id = device.get(
        "active_request_id"
    )

    if active_id:

        active_request = esim_requests.get(
            active_id
        )

    return {

        "provider":
            "MCOE",

        "device_id":
            device_id,

        "eid":
            device["eid"],

        "eid_status":
            device.get(
                "eid_status",
                "protected_or_unavailable"
            ),

        "status":
            device["esim_status"],

        "active_request_id":
            active_id,

        "esim_active":
            device["esim_status"] == "active",

        "smdp_address":
            SM_DP_PLUS_ADDRESS,

        "smdp_url":
            SM_DP_PLUS_URL,

        "matching_id":
            (
                active_request["matching_id"]
                if active_request
                else None
            ),

        "activation_code":
            (
                active_request["activation_code"]
                if active_request
                else None
            ),

        "profile":
            (
                active_request["profile_name"]
                if active_request
                else None
            )
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

            "ok":
                True,

            "message":
                "No active provisioning request."
        }

    esim_request = esim_requests.get(
        request_id
    )

    if esim_request:

        matching_id = esim_request["matching_id"]

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
# DEVELOPMENT DEVICE LIST
# =========================================================

@app.get("/api/devices")
def list_devices():

    safe_devices = []

    for device in devices.values():

        safe_devices.append({

            "device_id":
                device["device_id"],

            "device_name":
                device["device_name"],

            "online":
                device["online"],

            "registered_at":
                device["registered_at"],

            "last_seen":
                device["last_seen"],

            "eid":
                device["eid"],

            "eid_status":
                device.get(
                    "eid_status",
                    "protected_or_unavailable"
                ),

            "esim_status":
                device["esim_status"],

            "active_request_id":
                device["active_request_id"]
        })

    return {

        "count":
            len(safe_devices),

        "devices":
            safe_devices
    }


# =========================================================
# DEVELOPMENT REQUEST LIST
# =========================================================

@app.get("/api/esim/requests")
def list_esim_requests():

    safe_requests = []

    for request in esim_requests.values():

        safe_requests.append({

            "request_id":
                request["request_id"],

            "device_id":
                request["device_id"],

            "eid":
                request["eid"],

            "eid_status":
                request.get(
                    "eid_status",
                    "protected_or_unavailable"
                ),

            "matching_id":
                request["matching_id"],

            "profile_name":
                request["profile_name"],

            "profile_file":
                request["profile_file"],

            "smdp_address":
                request["smdp_address"],

            "smdp_url":
                request["smdp_url"],

            "activation_code":
                request["activation_code"],

            "status":
                request["status"],

            "created_at":
                request["created_at"],

            "updated_at":
                request["updated_at"]
        })

    return {

        "count":
            len(safe_requests),

        "requests":
            safe_requests
    }


# =========================================================
# RELEASE TEST PROFILE
# =========================================================

@app.post(
    "/api/esim/profile/{matching_id}/release"
)
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

    for request in esim_requests.values():

        if (
            request["matching_id"] == matching_id
            and request["status"]
            in (
                "pending",
                "provisioning",
                "active"
            )
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    "Profile is associated with an active "
                    "or provisioning request."
                )
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
