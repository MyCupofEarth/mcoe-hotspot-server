from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
import secrets
import os


# =========================================================
# MCOE eSIM PROVISIONING API
# =========================================================

app = FastAPI(
    title="MCOE eSIM Provisioning API",
    version="4.0.0"
)


# =========================================================
# CONFIGURATION
# =========================================================

# Your separate pySim SM-DP+ Render service.
#
# IMPORTANT:
# Do not put https:// here.
# The API will add it when returning the URL.
#
SM_DP_PLUS_ADDRESS = os.getenv(
    "SM_DP_PLUS_ADDRESS",
    "mcoe-sm-dp-pysim.onrender.com"
)

SM_DP_PLUS_URL = (
    "https://" + SM_DP_PLUS_ADDRESS
)


# =========================================================
# TEMPORARY STORAGE
# =========================================================
#
# These are in-memory only.
#
# Render can restart/redeploy the service, which means
# this data can be lost.
#
# For production we should move this to PostgreSQL.
#

devices = {}

esim_requests = {}

test_profiles = {
    "MCOE-TEST-001": {
        "matching_id": "MCOE-TEST-001",
        "profile_name": "MCOE Authorized Test Profile",
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

    return datetime.now(
        timezone.utc
    ).isoformat()


def generate_device_token():

    return secrets.token_urlsafe(32)


def generate_request_id():

    return (
        "MCOE-"
        + secrets.token_hex(16).upper()
    )


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
            "4.0.0",

        "service":
            "MCOE API",

        "smdp_plus":
            SM_DP_PLUS_URL
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {

        "status":
            "healthy",

        "server":
            "MCOE eSIM Provisioning API",

        "timestamp":
            utc_now(),

        "smdp_plus":
            SM_DP_PLUS_URL
    }


# =========================================================
# SM-DP+ CONFIGURATION
# =========================================================
#
# This does NOT perform an eSIM download.
#
# It tells the MCOE application which SM-DP+
# is associated with the provisioning system.
#

@app.get("/api/esim/smdp")
def smdp_configuration():

    return {

        "provider":
            "MCOE",

        "smdp_address":
            SM_DP_PLUS_ADDRESS,

        "smdp_url":
            SM_DP_PLUS_URL,

        "protocol":
            "GSMA RSP / ES9+",

        "status":
            "configured"
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

    # -----------------------------------------------------
    # EXISTING DEVICE
    # -----------------------------------------------------

    existing_device = devices.get(
        device_id
    )

    if existing_device:

        existing_device["device_name"] = (
            device_name
        )

        existing_device["online"] = True

        existing_device["last_seen"] = (
            utc_now()
        )

        return {

            "registered":
                True,

            "existing":
                True,

            "device_id":
                device_id,

            "device_token":
                existing_device["device_token"],

            "eid":
                existing_device["eid"],

            "esim_status":
                existing_device["esim_status"]
        }

    # -----------------------------------------------------
    # NEW DEVICE
    # -----------------------------------------------------

    device_token = generate_device_token()

    devices[device_id] = {

        "device_id":
            device_id,

        "device_name":
            device_name,

        "device_token":
            device_token,

        "online":
            True,

        "registered_at":
            utc_now(),

        "last_seen":
            utc_now(),

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
            device_token,

        "eid":
            None,

        "esim_status":
            "not_provisioned"
    }


# =========================================================
# DEVICE HEARTBEAT
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

    if (
        device["device_token"]
        != request.device_token
    ):

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

    device = devices.get(
        device_id
    )

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

        "esim_status":
            device["esim_status"],

        "active_request_id":
            device["active_request_id"]
    }


# =========================================================
# UPDATE DEVICE EID
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

    if not eid:

        raise HTTPException(
            status_code=400,
            detail="EID is required"
        )

    # Basic EID validation.
    #
    # EIDs are normally 32 decimal digits.
    #

    if (
        len(eid) != 32
        or not eid.isdigit()
    ):

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
# AVAILABLE TEST PROFILES
# =========================================================
#
# Development/test visibility.
#
# This does NOT expose the actual profile package.
#

@app.get("/api/esim/profiles")
def list_profiles():

    profiles = []

    for profile in test_profiles.values():

        profiles.append({

            "matching_id":
                profile["matching_id"],

            "profile_name":
                profile["profile_name"],

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
# eSIM PROVISION REQUEST
# =========================================================
#
# Creates an MCOE provisioning request.
#
# This does NOT directly install an eSIM.
#
# The authorized eUICC/LPA performs the actual RSP
# communication with the SM-DP+.
#

@app.post("/api/esim/provision")
def request_esim_provision(
    request: ProvisionRequest
):

    device_id = request.device_id.strip()

    device = devices.get(
        device_id
    )

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
    # PREVENT DUPLICATE ACTIVE REQUEST
    # -----------------------------------------------------

    active_request_id = (
        device.get("active_request_id")
    )

    if active_request_id:

        active_request = esim_requests.get(
            active_request_id
        )

        if active_request:

            if active_request["status"] in (
                "pending",
                "provisioning"
            ):

                return {

                    "provider":
                        "MCOE",

                    "request_id":
                        active_request_id,

                    "device_id":
                        device_id,

                    "eid":
                        device["eid"],

                    "status":
                        active_request["status"],

                    "smdp_address":
                        SM_DP_PLUS_ADDRESS,

                    "matching_id":
                        active_request["matching_id"],

                    "message":
                        "Existing eSIM provisioning request"
                }

    # -----------------------------------------------------
    # FIND AUTHORIZED AVAILABLE PROFILE
    # -----------------------------------------------------

    profile = None

    for candidate in test_profiles.values():

        if candidate["status"] == "available":

            profile = candidate

            break

    if not profile:

        raise HTTPException(
            status_code=503,
            detail=(
                "No authorized test eSIM profile "
                "is currently available"
            )
        )

    # -----------------------------------------------------
    # CREATE REQUEST
    # -----------------------------------------------------

    request_id = generate_request_id()

    matching_id = profile[
        "matching_id"
    ]

    created_at = utc_now()

    esim_requests[request_id] = {

        "request_id":
            request_id,

        "device_id":
            device_id,

        "eid":
            device["eid"],

        "matching_id":
            matching_id,

        "smdp_address":
            SM_DP_PLUS_ADDRESS,

        "smdp_url":
            SM_DP_PLUS_URL,

        "status":
            "pending",

        "created_at":
            created_at,

        "updated_at":
            created_at
    }

    # -----------------------------------------------------
    # RESERVE PROFILE
    # -----------------------------------------------------

    profile["status"] = "reserved"

    # -----------------------------------------------------
    # UPDATE DEVICE
    # -----------------------------------------------------

    device["esim_status"] = (
        "provisioning"
    )

    device["active_request_id"] = (
        request_id
    )

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

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

        "message":
            (
                "Authorized MCOE test profile "
                "reserved for this device"
            )
    }


# =========================================================
# eSIM REQUEST STATUS
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

    device = devices.get(
        device_id
    )

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
# CANCEL eSIM PROVISIONING
# =========================================================

@app.post("/api/esim/cancel")
def cancel_esim_provision(
    request: CancelProvisionRequest
):

    device_id = request.device_id.strip()

    device = devices.get(
        device_id
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
                "No active eSIM provisioning request"
        }

    esim_request = esim_requests.get(
        request_id
    )

    if not esim_request:

        device["active_request_id"] = None
        device["esim_status"] = (
            "not_provisioned"
        )

        return {

            "ok":
                True,

            "message":
                "Provisioning request no longer exists"
        }

    # -----------------------------------------------------
    # Release reserved profile
    # -----------------------------------------------------

    matching_id = esim_request[
        "matching_id"
    ]

    profile = test_profiles.get(
        matching_id
    )

    if profile:

        if profile["status"] == "reserved":

            profile["status"] = "available"

    # -----------------------------------------------------
    # Update request
    # -----------------------------------------------------

    esim_request["status"] = (
        "cancelled"
    )

    esim_request["updated_at"] = (
        utc_now()
    )

    # -----------------------------------------------------
    # Update device
    # -----------------------------------------------------

    device["active_request_id"] = None

    device["esim_status"] = (
        "not_provisioned"
    )

    return {

        "ok":
            True,

        "request_id":
            request_id,

        "device_id":
            device_id,

        "status":
            "cancelled"
    }


# =========================================================
# ADMIN / DEVELOPMENT DEVICE LIST
# =========================================================
#
# DEVELOPMENT ONLY.
#
# Add authentication before production use.
#

@app.get("/api/devices")
def list_devices():

    return {

        "count":
            len(devices),

        "devices":
            list(devices.values())
    }


# =========================================================
# ADMIN / DEVELOPMENT eSIM REQUEST LIST
# =========================================================

@app.get("/api/esim/requests")
def list_esim_requests():

    return {

        "count":
            len(esim_requests),

        "requests":
            list(esim_requests.values())
    }


# =========================================================
# DEVELOPMENT: SET PROFILE AVAILABLE
# =========================================================
#
# This is useful for testing after cancelling a request.
#
# Production should use authenticated administration.
#

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
