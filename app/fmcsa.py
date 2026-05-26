import logging

import httpx

from app.config import get_settings
from app.schemas import CarrierVerifyResponse

logger = logging.getLogger(__name__)

FMCSA_BASE = "https://mobile.fmcsa.dot.gov/qc/services"


async def verify_carrier(mc_number: str) -> CarrierVerifyResponse:
    """Verify a carrier by MC number against FMCSA. Returns eligibility."""
    settings = get_settings()

    clean_mc = mc_number.upper().replace("MC-", "").replace("MC", "").strip()
    if not clean_mc.isdigit():
        return CarrierVerifyResponse(
            mc_number=mc_number,
            eligible=False,
            reason="Invalid MC number format",
        )

    if settings.allow_mock_fmcsa:
        return _mock_response(clean_mc)

    url = f"{FMCSA_BASE}/carriers/docket-number/{clean_mc}"
    params = {"webKey": settings.fmcsa_webkey}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        logger.exception("FMCSA request failed")
        return CarrierVerifyResponse(
            mc_number=clean_mc,
            eligible=False,
            reason=f"FMCSA API error: {type(e).__name__}",
        )

    return _parse_fmcsa_response(clean_mc, data)


def _parse_fmcsa_response(mc: str, data: dict) -> CarrierVerifyResponse:
    """Parse FMCSA response. Structure varies — defensive parsing required."""
    content = data.get("content") if isinstance(data, dict) else None
    if not content:
        return CarrierVerifyResponse(
            mc_number=mc,
            eligible=False,
            reason="Carrier not found in FMCSA database",
        )

    record = content[0] if isinstance(content, list) and content else content
    carrier = record.get("carrier", record) if isinstance(record, dict) else {}

    allowed = carrier.get("allowedToOperate", "").upper() == "Y"
    oos = carrier.get("oosDate") not in (None, "", "null")
    status = "ACTIVE" if allowed and not oos else "INACTIVE"

    return CarrierVerifyResponse(
        mc_number=mc,
        eligible=allowed and not oos,
        carrier_name=carrier.get("legalName") or carrier.get("dbaName"),
        dot_number=str(carrier.get("dotNumber", "")),
        status=status,
        reason=None if (allowed and not oos) else "Carrier not authorized or out of service",
    )


def _mock_response(mc: str) -> CarrierVerifyResponse:
    """For local dev when FMCSA key is unavailable."""
    if mc.startswith("9"):
        return CarrierVerifyResponse(
            mc_number=mc,
            eligible=False,
            reason="Mock: not eligible (MC starts with 9)",
        )
    return CarrierVerifyResponse(
        mc_number=mc,
        eligible=True,
        carrier_name=f"Test Carrier {mc}",
        dot_number="1234567",
        status="ACTIVE",
    )
