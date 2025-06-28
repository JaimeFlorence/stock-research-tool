import pytest
import os
import json
from config_manager import ConfigManager

#// These are tests.

@pytest.fixture
def config_manager(tmp_path):
    config_path = tmp_path / "config.json"
    return ConfigManager(config_path=str(config_path))

def test_initial_config(config_manager):
    assert config_manager.get_fmp_api_key() == "abk6plYKMETVpKxgnsi6O3HAuQAktazC"
    assert config_manager.get_sector_params("Technology") == {
        "growth_rate": 0.08, "pe_ratio": 25.0, "discount_rate": 0.10
    }

def test_set_fmp_api_key(config_manager):
    config_manager.set_fmp_api_key("new_key")
    assert config_manager.get_fmp_api_key() == "new_key"
    with open(config_manager.config_path, 'r') as f:
        config = json.load(f)
        assert config["fmp_api_key"] == "new_key"

def test_set_sector_params(config_manager):
    config_manager.set_sector_params("Technology", growth_rate=0.09, pe_ratio=26.0)
    params = config_manager.get_sector_params("Technology")
    assert params["growth_rate"] == 0.09
    assert params["pe_ratio"] == 26.0
    assert params["discount_rate"] == 0.10  # unchanged

def test_random_seed_generate(config_manager):
    config_manager.set_random_seed_mode("generate")
    seed1 = config_manager.get_random_seed()
    seed2 = config_manager.get_random_seed()
    assert isinstance(seed1, int)
    assert seed1 != seed2  # New seed each time

def test_random_seed_reuse(config_manager):
    config_manager.set_random_seed_mode("generate")
    seed1 = config_manager.get_random_seed()
    config_manager.set_random_seed_mode("reuse")
    seed2 = config_manager.get_random_seed()
    assert seed1 == seed2  # Same seed reused

def test_random_seed_specify(config_manager):
    config_manager.set_random_seed_mode("specify", value=42)
    seed = config_manager.get_random_seed()
    assert seed == 42

def test_invalid_seed_mode(config_manager):
    with pytest.raises(ValueError):
        config_manager.set_random_seed_mode("invalid")