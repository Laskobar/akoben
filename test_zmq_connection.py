from src.agents.execution.mt5_connector import MT5Connector

# Test script
connector = MT5Connector()
if connector.connect():
    price = connector.get_current_price("US30")
    print(f"US30 price: {price}")
connector.disconnect()
