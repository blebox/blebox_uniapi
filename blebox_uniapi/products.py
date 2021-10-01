from .box import Box


class Products:

    @staticmethod
    async def async_from_host(api_host):
        path = "/api/device/state"
        box_info = await api_host.async_api_get(path)
        entities_data = await Products.get_entity_data(api_host)

        product = Products.from_data(api_host, box_info, entities_data)
        return product

    @staticmethod
    def from_data(api_host, root_info, entities_data):
        info = root_info.get("device", root_info)

        return Box(api_host, info, entities_data)

    @staticmethod
    async def get_entity_data(api_host):
        try:
            results = await api_host.async_api_get('/state')
        except:
            # It's really bad idea to catch all exceptions but because of chanage
            # in call order for dynamic sensors for now I can't predict/know all
            # possible cases for old and new devices
            results = None

        return results
