# Boliq for Home Assistant

Control your [Boliq](https://boliq.co.uk) automatic bollards from Home Assistant.

* Each bollard is a **gate**. **Open means lowered** (cars can pass) and **closed means raised**.
* Raise is only offered if you ticked **Allow raising** when connecting.
* Each bollard also has an **online** sensor and, for battery bollards, a **battery** level.
* Bollards are read every 30 seconds, and every 5 seconds while one is moving. A move is confirmed when the bollard next checks in with Boliq.

Boliq bollards are access control, not crash rated barriers.

## Install

1. In Home Assistant open **HACS**, the three dots menu, **Custom repositories**.
2. Add `https://github.com/Boliqltd/boliq-home-assistant` with type **Integration**.
3. Search HACS for **Boliq**, press **Download**, then restart Home Assistant.

## Set up

1. Get the Boliq Client ID and Client Secret from https://boliq.co.uk/home-assistant.html.
2. **Settings**, **Devices & services**, the three dots menu, **Application credentials**, **Add application credential**: choose Boliq and paste them.
3. **Settings**, **Devices & services**, **Add integration**, **Boliq**. Sign in with your Boliq login, choose your bollards and press **Connect**.

You can change which bollards Home Assistant can use, or disconnect it, in Connected apps in your Boliq account.

## Support

Email hello@boliq.co.uk.

## Development

Tests use Home Assistant's test kit and need Python 3.13:

```bash
pip install pytest-homeassistant-custom-component
pytest
```
