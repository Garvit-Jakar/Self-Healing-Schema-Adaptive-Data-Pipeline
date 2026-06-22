import pandas as pd
import json
import random
from datetime import date

today = date.today().strftime("%Y-%m-%d")

def generate_mock_data(day: int = 1) -> list[dict]:
    """Generate mock ad campaign JSON data. On day 5+, introduce schema drift."""
    
    base_data = [
        {
            "campaign_id": f"camp_{i}",
            "campaign_name": f"Summer Campaign {i}",
            "budget": round(random.uniform(500, 5000), 2),
            "impressions": random.randint(1000, 100000),
            "clicks": random.randint(50, 5000),
            "date": today
        }
        for i in range(1, 11)
    ]
    
    # Chaos Monkey kicks in on day 5
    if day >= 5:
        print("🐒 Chaos Monkey activated! Introducing schema drift...")
        for record in base_data:
            record["id_campaign"] = record.pop("campaign_id")   # renamed field
            record["budget"] = f"${record['budget']:,.2f}"      # float → string
    
    return base_data


if __name__ == "__main__":
    data = generate_mock_data(day=1)
    print(json.dumps(data[:2], indent=2))