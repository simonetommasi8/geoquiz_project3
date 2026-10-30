from geoquiz.cleaning import build_countries_table

countries = build_countries_table()

print(countries.shape)
print(countries.loc["ITA"])
