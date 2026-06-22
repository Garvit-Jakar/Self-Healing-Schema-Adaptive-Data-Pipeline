import pandas as pd

def patch_dataframe(df):
    # 1. Rename 'id_campaign' to 'campaign_id'
    if 'id_campaign' in df.columns:
        df = df.rename(columns={'id_campaign': 'campaign_id'})

    # 2. Convert 'budget' to float64
    if 'budget' in df.columns:
        # Remove '$' and ',' then convert to float
        df['budget'] = df['budget'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(float)

    # Ensure other columns have correct dtypes if they exist and are not already correct
    # (No explicit errors for these, but good to ensure)
    if 'impressions' in df.columns:
        df['impressions'] = df['impressions'].astype('int64')
    if 'clicks' in df.columns:
        df['clicks'] = df['clicks'].astype('int64')
    # 'campaign_name', 'campaign_id', 'date' are expected as 'object' (string) which is often default

    return df
