import duckdb

con = duckdb.connect("pipeline.duckdb")

print("\n📊 Tables in database:")
print(con.execute("SHOW TABLES").fetchdf())

print("\n📋 All records in ad_campaigns:")
df = con.execute("SELECT * FROM ad_campaigns").fetchdf()
print(df.to_string(index=False))

print(f"\n Total rows: {len(df)}")
con.close()