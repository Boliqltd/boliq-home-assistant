"""Sign in with Boliq (OAuth 2.0 through the Connect to Boliq page, with PKCE)."""

from homeassistant.components.application_credentials import (
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .const import AUTHORIZE_URL, TOKEN_URL


class BoliqImplementation(config_entry_oauth2_flow.LocalOAuth2ImplementationWithPkce):
    """Boliq sign in. PKCE means a code caught on the way back is useless to anyone else."""

    def __init__(self, hass: HomeAssistant, auth_domain: str, credential: ClientCredential) -> None:
        super().__init__(
            hass,
            auth_domain,
            credential.client_id,
            AUTHORIZE_URL,
            TOKEN_URL,
            client_secret=credential.client_secret,
        )
        self._name = credential.name

    @property
    def name(self) -> str:
        """Name shown when more than one credential exists."""
        return self._name or "Boliq"


async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential: ClientCredential
) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
    """Return Boliq's sign in."""
    return BoliqImplementation(hass, auth_domain, credential)


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Boliq's authorisation server (used only if the above is not)."""
    return AuthorizationServer(authorize_url=AUTHORIZE_URL, token_url=TOKEN_URL)


async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]:
    """Words for the credentials dialog."""
    return {
        "developers_url": "https://boliq.co.uk/home-assistant.html",
        "redirect_url": "https://my.home-assistant.io/redirect/oauth",
    }
