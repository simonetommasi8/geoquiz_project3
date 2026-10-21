from geoquiz.data import download_countries, load_countries

download_countries()
countries = load_countries()

print(f"Loaded {len(countries)} countries")
print(countries[0]["name"]["common"])
