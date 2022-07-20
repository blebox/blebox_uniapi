from random import choice

from blebox_uniapi.box_types import (
    BOX_TYPE_CONF,
    get_conf,
    get_conf_set,
    get_latest_api_level,
    get_latest_conf,
)


class TestBoxTypes:

    box_types = tuple(BOX_TYPE_CONF.keys())
    simple_conf_set = {5: {"tag": "first_entry"}, 10: {"tag": "second_entry"}}

    async def test_get_conf_set_valid(self):
        conf_set = get_conf_set(choice(self.box_types))

        assert isinstance(conf_set, dict)
        assert conf_set != {}

    async def test_get_conf_set_invalid(self):
        conf_set = get_conf_set("nonexistent_type")

        assert isinstance(conf_set, dict)
        assert conf_set == {}

    async def test_get_conf_valid(self):
        """Test choosing functionality of get_conf function on exemplary conf_set."""
        for api_level, tag_value in (
            (5, "first_entry"),  # a marginal example
            (7, "first_entry"),  # 'in between' example
            (10, "second_entry"),  # a marginal example
            (17, "second_entry"),  # future example
        ):
            conf = get_conf(api_level, self.simple_conf_set)

            assert isinstance(conf, dict)
            assert conf["tag"] == tag_value

    async def test_get_conf_invalid(self):
        conf = get_conf(3, self.simple_conf_set)  # not supported example

        assert isinstance(conf, dict)
        assert conf == {}

    async def test_get_latest_conf_valid(self):
        conf = get_latest_conf(choice(self.box_types))

        assert isinstance(conf, dict)
        assert conf != {}

    async def test_get_latest_conf_invalid(self):
        conf = get_latest_conf("nonexistent_type")

        assert isinstance(conf, dict)
        assert conf == {}

    async def test_get_latest_api_level_valid(self):
        api_level = get_latest_api_level(choice(self.box_types))

        assert isinstance(api_level, int)
        assert api_level

    async def test_get_latest_api_level_invalid(self):
        api_level = get_latest_api_level("nonexistent_type")

        assert isinstance(api_level, int)
        assert not api_level
