from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed


class InnovaCoordinator(DataUpdateCoordinator[Any]):
    def __init__(
        self,
        hass: HomeAssistant,
        innova: Any,
        logger: logging.Logger,
        name: str,
        update_interval: timedelta,
    ):
        self.innova = innova

        super().__init__(hass, logger, name=name, update_interval=update_interval)

    async def _async_update_data(self) -> Any:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        success = await self.innova.async_update()
        if not success:
            raise UpdateFailed("Innova connection issue")
        
        return self.innova
