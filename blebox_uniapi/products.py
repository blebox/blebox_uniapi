from .box import Box


class Products:

    @staticmethod
    async def async_from_host(api_host):
        path = "/api/device/state"
        data = await api_host.async_api_get(path)
        product = Products.from_data(data, api_host)
        return product

    @staticmethod
    def from_data(root, api_host):
        info = root.get("device", root)

        return Box(api_host, info)
