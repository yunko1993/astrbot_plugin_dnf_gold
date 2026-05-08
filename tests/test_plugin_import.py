import importlib
import sys
import types
import unittest
from pathlib import Path


def install_astrbot_stubs():
    astrbot = types.ModuleType("astrbot")
    api = types.ModuleType("astrbot.api")
    event = types.ModuleType("astrbot.api.event")
    star = types.ModuleType("astrbot.api.star")
    core = types.ModuleType("astrbot.core")
    platform = types.ModuleType("astrbot.core.platform")

    class FilterStub:
        @staticmethod
        def command(_name):
            def decorator(func):
                return func

            return decorator

    class StarStub:
        def __init__(self, context):
            self.context = context

    def register(*_args, **_kwargs):
        def decorator(cls):
            return cls

        return decorator

    event.filter = FilterStub()
    star.Context = object
    star.Star = StarStub
    star.register = register
    platform.AstrMessageEvent = object

    sys.modules.update(
        {
            "astrbot": astrbot,
            "astrbot.api": api,
            "astrbot.api.event": event,
            "astrbot.api.star": star,
            "astrbot.core": core,
            "astrbot.core.platform": platform,
        }
    )


class PluginImportTest(unittest.TestCase):
    def test_main_imports_as_package_module(self):
        install_astrbot_stubs()
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        try:
            module = importlib.import_module("astrbot_plugin_dnf_gold_remote.main")
        finally:
            sys.path.pop(0)

        self.assertTrue(hasattr(module, "DnfGoldPlugin"))
        self.assertEqual(
            "astrbot_plugin_dnf_gold_remote.yxdr_source",
            module.fetch_yxdr_offers.__module__,
        )


if __name__ == "__main__":
    unittest.main()
