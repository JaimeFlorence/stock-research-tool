import os
import json
from datetime import datetime
import pytz
import random
import uuid

class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.default_config = {
            "fmp_api_key": "abk6plYKMETVpKxgnsi6O3HAuQAktazC",
            "sectors": {
                "Technology": {"growth_rate": 0.08, "pe_ratio": 25.0, "discount_rate": 0.10},
                "Healthcare": {"growth_rate": 0.06, "pe_ratio": 20.0, "discount_rate": 0.09},
                "Financials": {"growth_rate": 0.04, "pe_ratio": 15.0, "discount_rate": 0.08},
                "Consumer Discretionary": {"growth_rate": 0.05, "pe_ratio": 18.0, "discount_rate": 0.09},
                "Consumer Staples": {"growth_rate": 0.03, "pe_ratio": 16.0, "discount_rate": 0.07},
                "Energy": {"growth_rate": 0.04, "pe_ratio": 12.0, "discount_rate": 0.10},
                "Utilities": {"growth_rate": 0.02, "pe_ratio": 14.0, "discount_rate": 0.06},
                "Industrials": {"growth_rate": 0.04, "pe_ratio": 17.0, "discount_rate": 0.08},
                "Materials": {"growth_rate": 0.04, "pe_ratio": 15.0, "discount_rate": 0.09},
                "Real Estate": {"growth_rate": 0.03, "pe_ratio": 16.0, "discount_rate": 0.07},
                "Communication Services": {"growth_rate": 0.06, "pe_ratio": 20.0, "discount_rate": 0.09}
            },
            "random_seed": {
                "mode": "generate",
                "value": None,
                "last_used": None
            },
            "last_updated": self._get_pdt_timestamp()
        }
        self.config = self.load_config()

    def _get_pdt_timestamp(self):
        return datetime.now(pytz.timezone("America/Los_Angeles")).isoformat()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                config["last_updated"] = self._get_pdt_timestamp()
                return config
        self.save_config(self.default_config)
        return self.default_config

    def save_config(self, config):
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
        config["last_updated"] = self._get_pdt_timestamp()

    def get_fmp_api_key(self):
        return self.config["fmp_api_key"]

    def set_fmp_api_key(self, api_key):
        self.config["fmp_api_key"] = api_key
        self.save_config(self.config)

    def get_sector_params(self, sector):
        return self.config["sectors"].get(sector, {})

    def set_sector_params(self, sector, growth_rate=None, pe_ratio=None, discount_rate=None):
        if sector not in self.config["sectors"]:
            self.config["sectors"][sector] = {}
        params = self.config["sectors"][sector]
        if growth_rate is not None:
            params["growth_rate"] = growth_rate
        if pe_ratio is not None:
            params["pe_ratio"] = pe_ratio
        if discount_rate is not None:
            params["discount_rate"] = discount_rate
        self.save_config(self.config)

    def get_random_seed(self):
        mode = self.config["random_seed"]["mode"]
        if mode == "reuse" and self.config["random_seed"]["last_used"] is not None:
            return self.config["random_seed"]["last_used"]
        elif mode == "specify":
            return self.config["random_seed"]["value"]
        else:  # generate
            seed = random.randint(0, 1000000)
            self.config["random_seed"]["last_used"] = seed
            self.save_config(self.config)
            return seed

    def set_random_seed_mode(self, mode, value=None):
        if mode not in ["reuse", "specify", "generate"]:
            raise ValueError("Invalid mode. Use 'reuse', 'specify', or 'generate'.")
        self.config["random_seed"]["mode"] = mode
        if mode == "specify" and value is not None:
            self.config["random_seed"]["value"] = value
        self.save_config(self.config)