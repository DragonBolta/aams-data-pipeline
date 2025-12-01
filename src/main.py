from readers import csv_reader
from src.clean import clean
from src.load import load_into_db

df = csv_reader.read_csv("../data/Ask A Manager Salary Survey 2021 (Responses) - Form Responses 1.csv")
df = clean(df)
print(df)
load_into_db(df)
