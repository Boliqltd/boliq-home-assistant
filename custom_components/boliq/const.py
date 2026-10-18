"""Constants for the Boliq integration."""

DOMAIN = "boliq"

BASE_URL = "https://boliq.co.uk"
API_URL = f"{BASE_URL}/api/v1"
AUTHORIZE_URL = f"{BASE_URL}/connect.html"
TOKEN_URL = f"{BASE_URL}/api/oauth/token"

# Lowering, and raising if the owner ticks Allow raising on Connect to Boliq
# (and Boliq has switched raising on for Home Assistant).
SCOPES = ["devices:control", "devices:raise"]

# How often to read the bollards. The API allows 60 requests a minute per
# link, and a moving bollard is read more often until it reports back.
UPDATE_INTERVAL_S = 30
MOVING_INTERVAL_S = 5

LOWERED = "lowered"
RAISED = "raised"
