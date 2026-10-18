"""Boliq in Home Assistant: sign in, bollards as covers, moving them, signing in again.

Run from home-assistant/: pytest (needs pytest-homeassistant-custom-component).
"""

from http import HTTPStatus
import time
from urllib.parse import parse_qs, urlparse

import pytest

from homeassistant import config_entries
from homeassistant.components.application_credentials import ClientCredential, async_import_client_credential
from homeassistant.components.cover import CoverEntityFeature
from homeassistant.const import ATTR_ENTITY_ID, ATTR_SUPPORTED_FEATURES
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceNotSupported
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.boliq.const import API_URL, AUTHORIZE_URL, DOMAIN, TOKEN_URL

CLIENT_ID = "blq_client_ha"
CLIENT_SECRET = "blq_secret_ha"
LINK = "11111111-1111-1111-1111-111111111111"
FRONT = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SIDE = "cccccccc-cccc-cccc-cccc-cccccccccccc"


def device(id_, label, position, battery=None, status="online", raise_=False, pending=None):
    return {
        "id": id_, "label": label, "code": "BLQ-" + id_[:8].upper(), "status": status, "position": position,
        "position_source": "sensor", "pending_position": pending, "battery_pct": battery,
        "last_seen_at": "2026-10-18T10:00:00Z", "fault": None, "firmware_version": "1.2.0", "sandbox": False,
        "connection": {"id": LINK, "via": "owner", "partner_reference": None},
        "permissions": {"control": True, "raise": raise_, "schedules_write": False},
    }


DEVICES = {"data": [device(FRONT, "Front gate", "lowered", battery=88), device(SIDE, "Side gate", "raised", raise_=True)]}


@pytest.fixture
async def credentials(hass: HomeAssistant) -> None:
    assert await async_setup_component(hass, "application_credentials", {})
    await async_import_client_credential(hass, DOMAIN, ClientCredential(CLIENT_ID, CLIENT_SECRET), DOMAIN)


def token(expires_in=3600):
    return {"access_token": "blq_at_test", "refresh_token": "blq_rt_test", "token_type": "Bearer", "expires_in": expires_in, "expires_at": time.time() + expires_in}


@pytest.fixture
async def entry(hass: HomeAssistant, credentials, aioclient_mock) -> MockConfigEntry:
    aioclient_mock.get(f"{API_URL}/devices", json=DEVICES)
    e = MockConfigEntry(domain=DOMAIN, unique_id=LINK, title="Boliq", data={"auth_implementation": DOMAIN, "token": token()})
    e.add_to_hass(hass)
    assert await hass.config_entries.async_setup(e.entry_id)
    await hass.async_block_till_done()
    return e


async def test_sign_in_with_boliq(hass: HomeAssistant, credentials, hass_client_no_auth, aioclient_mock, current_request_with_host) -> None:
    """The owner is sent to Connect to Boliq with PKCE and the scopes, and one entry is made per link."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == "external"
    url = urlparse(result["url"])
    query = parse_qs(url.query)
    assert f"{url.scheme}://{url.netloc}{url.path}" == AUTHORIZE_URL
    assert query["client_id"] == [CLIENT_ID]
    assert query["scope"] == ["devices:control devices:raise"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["code_challenge"][0]
    state = config_entry_oauth2_flow._encode_jwt(hass, {"flow_id": result["flow_id"], "redirect_uri": "https://example.com/auth/external/callback"})
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=blq_code_x&state={state}")
    assert resp.status == HTTPStatus.OK

    aioclient_mock.post(TOKEN_URL, json=token())
    aioclient_mock.get(f"{API_URL}/devices", json=DEVICES)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] == "create_entry"
    assert result["result"].unique_id == LINK
    sent = [c for c in aioclient_mock.mock_calls if str(c[1]) == TOKEN_URL][0][2]
    assert sent["code_verifier"], "PKCE verifier goes with the code"
    assert sent["client_secret"] == CLIENT_SECRET

    # signing in again for the same link does not make a second entry
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    state = config_entry_oauth2_flow._encode_jwt(hass, {"flow_id": result["flow_id"], "redirect_uri": "https://example.com/auth/external/callback"})
    await client.get(f"/auth/external/callback?code=blq_code_y&state={state}")
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_bollards_are_covers_open_means_lowered(hass: HomeAssistant, entry) -> None:
    front = hass.states.get("cover.front_gate")
    side = hass.states.get("cover.side_gate")
    assert front.state == "open"
    assert front.attributes["current_position"] == 100
    assert front.attributes["device_class"] == "gate"
    assert side.state == "closed"
    assert side.attributes["current_position"] == 0
    # raising only where the owner ticked Allow raising
    assert front.attributes[ATTR_SUPPORTED_FEATURES] == CoverEntityFeature.OPEN
    assert side.attributes[ATTR_SUPPORTED_FEATURES] == CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
    assert hass.states.get("binary_sensor.front_gate_connectivity").state == "on"
    assert hass.states.get("sensor.front_gate_battery").state == "88"
    assert hass.states.get("sensor.side_gate_battery") is None, "a mains bollard has no battery sensor"


async def test_lowering_and_raising_send_commands(hass: HomeAssistant, entry, aioclient_mock) -> None:
    aioclient_mock.post(f"{API_URL}/devices/{SIDE}/commands", status=202, json={"id": "c1", "state": "queued"})
    await hass.services.async_call("cover", "open_cover", {ATTR_ENTITY_ID: "cover.side_gate"}, blocking=True)
    await hass.services.async_call("cover", "close_cover", {ATTR_ENTITY_ID: "cover.side_gate"}, blocking=True)
    # the owner did not allow raising the front gate, so Home Assistant will not offer it
    with pytest.raises(ServiceNotSupported):
        await hass.services.async_call("cover", "close_cover", {ATTR_ENTITY_ID: "cover.front_gate"}, blocking=True)
    posts = [c for c in aioclient_mock.mock_calls if c[0] == "POST"]
    assert posts[0][2] == {"position": "lowered"}
    assert str(posts[0][1]).endswith(f"/devices/{SIDE}/commands")
    assert posts[0][3]["Idempotency-Key"].startswith("ha-")
    assert posts[1][2] == {"position": "raised"}
    assert len(posts) == 2


async def test_a_refused_command_is_shown_as_an_error(hass: HomeAssistant, entry, aioclient_mock) -> None:
    aioclient_mock.post(
        f"{API_URL}/devices/{SIDE}/commands", status=409,
        json={"error": {"code": "device_offline", "message": "This bollard is offline."}},
    )
    with pytest.raises(HomeAssistantError, match="This bollard is offline"):
        await hass.services.async_call("cover", "open_cover", {ATTR_ENTITY_ID: "cover.side_gate"}, blocking=True)


async def test_moving_bollard_reads_more_often_and_offline_shows(hass: HomeAssistant, entry, aioclient_mock) -> None:
    coordinator = entry.runtime_data
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{API_URL}/devices", json={"data": [device(FRONT, "Front gate", "lowered", status="offline", pending="raised"), device(SIDE, "Side gate", "raised")]})
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.update_interval.total_seconds() == 5
    assert hass.states.get("binary_sensor.front_gate_connectivity").state == "off"
    assert hass.states.get("cover.front_gate").state == "closing"


async def test_disconnected_in_boliq_asks_to_sign_in_again(hass: HomeAssistant, entry, aioclient_mock) -> None:
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{API_URL}/devices", status=401, json={"error": {"code": "connection_revoked", "message": "The owner has disconnected this app."}})
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress()
    assert any(f["context"]["source"] == config_entries.SOURCE_REAUTH for f in flows)
