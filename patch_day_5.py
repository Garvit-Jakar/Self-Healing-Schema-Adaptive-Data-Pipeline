import pandas as pd

def patch_dataframe(df):
    # 1. Rename 'id_campaign' to 'campaign_id'
    if 'id_campaign' in df.columns:
        df = df.rename(columns={'id_campaign': 'campaign_id'})

    # 2. Clean and convert 'budget' to float64
    if 'budget' in df.columns:
        df['budget'] = df['budget'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(float)

    return df
