from __future__ import print_function

from json import load
from os import path
from unittest import TestCase
from unittest import main as unittest_main

from pkg_resources import resource_filename

from offregister.marshmallow_parser.auth import AuthConfigSchema
from offregister.marshmallow_parser.register import RegisterConfig


class TestParser(TestCase):
    maxDiff = 3000

    def setUp(self):
        with open(
            path.join(
                path.dirname(resource_filename("offregister", "__main__.py")),
                "_config",
                "auth.sample.json",
            )
        ) as f:
            self.auth_sample = load(f)

        with open(
            path.join(
                path.dirname(resource_filename("offregister", "__main__.py")),
                "_config",
                "register.new.sample.json",
            )
        ) as f:
            self.register_new_sample = load(f)

    def test_auth_parse(self):
        schema = AuthConfigSchema()

        schema.load(self.auth_sample).data.name

        result = schema.dump(self.auth_sample)
        print("\nresult =", result.data["name"])
        self.assertDictEqual(result.data, self.auth_sample)

    def test_register_parse(self):
        schema = RegisterConfig()
        result = schema.dump(self.register_new_sample)
        self.assertDictEqual(result.data, self.register_new_sample)


if __name__ == "__main__":
    unittest_main()
