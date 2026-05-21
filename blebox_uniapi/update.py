from typing import Optional

from .feature import Feature


class Update(Feature):
    @property
    def installed_version(self) -> Optional[str]:
        return self._product.firmware_version

    @property
    def latest_version(self) -> Optional[str]:
        return self._product.available_firmware_version

    async def async_update(self) -> None:
        # OTA state is stored as Box attributes, not in last_data. async_update_data() won't trigger the OTA check.
        await self._product.async_ota_check()

    async def async_install(self) -> None:
        await self._product.async_ota_update()

    def after_update(self) -> None:
        pass
