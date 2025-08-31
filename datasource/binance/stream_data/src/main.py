import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from trading_core.utilities.LoadJsonConfig import LoadJsonConfig
from binance_streaming import binance_streaming

if __name__ == "__main__":
    config_path = os.getenv("CONFIG_PATH")
    config = LoadJsonConfig(config_path)
    binance_streaming(config)