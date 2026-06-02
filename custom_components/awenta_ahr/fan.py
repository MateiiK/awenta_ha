import logging

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.helpers.restore_state import RestoreEntity

from .entity import AwentaEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):

    data = hass.data[DOMAIN][entry.entry_id]

    api = data["api"]
    coordinator = data["coordinator"]

    entities = []

    for device in api.devices:

        entities.append(
            AwentaFan(coordinator, api, device["mac"], device["name"])
        )

    async_add_entities(entities)


LOGGER = logging.getLogger(__name__)


class AwentaFan(RestoreEntity, AwentaEntity, FanEntity):

    def __init__(self, coordinator, api, mac, name):

        super().__init__(coordinator, api, mac, name)

        self._attr_name = name
        self._attr_unique_id = f"{mac}_fan"
        self._attr_supported_features = (
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF
        )
        self._attr_speed_count = 3
        self._last_percentage: int | None = None

    @property
    def extra_state_attributes(self):
        """Return extra attributes for the state machine."""
        return {"last_percentage": self._last_percentage}

    @property
    def is_on(self):

        data = self.coordinator.data.get(self.mac, {})
        return data.get("recuperation_gear_adv", 0) > 0

    @property
    def percentage(self):

        gear = self.coordinator.data.get(self.mac, {}).get(
            "recuperation_gear_adv", 0
        )

        if gear == 0:
            return 0

        return int(gear / 3 * 100)

    async def async_set_percentage(self, percentage):

        if percentage == 0:
            await self.async_turn_off()
            return

        gear = max(1, min(3, round(percentage / 33)))

        # remember last non-zero percentage
        self._last_percentage = percentage

        LOGGER.debug("Setting fan %s to percentage %s (gear %s)", self.mac, percentage, gear)

        await self.api.send(
            self.mac,
            {
                "act": "send_gear_number",
                "gear_nr": gear,
            },
        )

        # Persist the updated attribute to HA state
        try:
            self.async_write_ha_state()
        except Exception:  # pragma: no cover - defensive
            LOGGER.exception("Failed to write HA state for %s", self.mac)

    async def async_turn_off(self, **kwargs):

        LOGGER.debug("Turning off fan %s", self.mac)

        await self.api.send(
            self.mac,
            {
                "act": "send_gear_number",
                "gear_nr": 0,
            },
        )

        # Ensure last_percentage remains persisted (do not clear it), update state
        try:
            self.async_write_ha_state()
        except Exception:  # pragma: no cover - defensive
            LOGGER.exception("Failed to write HA state for %s", self.mac)

    async def async_added_to_hass(self):
        await super().async_added_to_hass()

        # Restore last known percentage if available
        last_state = await self.async_get_last_state()
        if last_state is not None:
            try:
                # Prefer previously saved `last_percentage` attribute (persisted when we wrote state)
                last_pct = last_state.attributes.get("last_percentage")
                if not last_pct:
                    # Fallback to `percentage` if `last_percentage` not present
                    last_pct = last_state.attributes.get("percentage")

                if isinstance(last_pct, int) and last_pct > 0:
                    self._last_percentage = last_pct
                    LOGGER.debug("Restored last percentage %s for %s", last_pct, self.mac)
            except Exception:  # pragma: no cover - defensive
                LOGGER.exception("Failed to restore last state for %s", self.mac)

    async def async_turn_on(
        self,
        speed: str | int | None = None,
        percentage: int | None = None,
        **kwargs,
    ):
        """Turn the fan on.

        If a percentage is provided, delegate to `async_set_percentage`.
        If a speed is provided, map it to an equivalent percentage.
        Otherwise restore last known non-zero gear or set to gear 1.
        """

        if percentage is not None:
            await self.async_set_percentage(percentage)
            return

        if speed is not None:
            use_percentage = None
            if isinstance(speed, int):
                use_percentage = speed
            elif isinstance(speed, str):
                speed_lower = speed.lower()
                if speed_lower in {"low", "slow", "1"}:
                    use_percentage = 33
                elif speed_lower in {"medium", "med", "2"}:
                    use_percentage = 66
                elif speed_lower in {"high", "3"}:
                    use_percentage = 100
                else:
                    try:
                        use_percentage = int(speed_lower)
                    except ValueError:
                        use_percentage = None

            if use_percentage is not None:
                await self.async_set_percentage(use_percentage)
                return

        # Prefer the last remembered percentage, then device-reported gear, then default to 1
        if self._last_percentage is not None:
            use_percentage = self._last_percentage
        else:
            data = self.coordinator.data.get(self.mac, {})
            gear = data.get("recuperation_gear_adv", 0) or 1
            use_percentage = int(gear / 3 * 100)

        await self.async_set_percentage(use_percentage)