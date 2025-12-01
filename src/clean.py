from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import pandas as pd
from readers.csv_reader import read_csv
import country_converter as coco

def clean(df):

    rename_columns = {
        "How old are you?": "age",
        "What industry do you work in?": "industry",
        "Job title": "job_title",
        "If your job title needs additional context, please clarify here:": "job_context",
        "What is your annual salary? (You'll indicate the currency in a later question. If you are part-time or hourly, please enter an annualized equivalent -- what you would earn if you worked the job 40 hours a week, 52 weeks a year.)": "salary",
        "How much additional monetary compensation do you get, if any (for example, bonuses or overtime in an average year)? Please only include monetary compensation here, not the value of benefits.": "bonus",
        "Please indicate the currency": "currency",
        "If your income needs additional context, please provide it here:": "income_text",
        "What country do you work in?": "country",
        "If you're in the U.S., what state do you work in?": "us_state",
        "What city do you work in?": "city"
    }

    df = df.rename(columns=rename_columns)
    salary_column = 'salary'
    bonus_column = 'bonus'

    df[salary_column] = df[salary_column].replace(',', '')
    df[salary_column] = pd.to_numeric(df[salary_column], errors="coerce")
    df[salary_column] = df[salary_column].fillna(0).astype(int)

    df[bonus_column] = df[bonus_column].replace(',', '')
    df[bonus_column] = pd.to_numeric(df[bonus_column], errors="coerce")
    df[bonus_column] = df[bonus_column].fillna(0).astype(int)

    # df[bonus_column] = df['']

    df['age'] = df['age'].astype(str).str.extract(r'^(\d+)').fillna(0).astype(int)

    cc = coco.CountryConverter()

    df['country'] = cc.pandas_convert(series=df['country'], to='ISO3', not_found=None)
    df = df.dropna(subset=['country'])
    df = df[df['country'].astype(str).str.match(r'^[A-Z]{3}$')]


    return df


# job_titles = [
#     'Director',
#     'Manager',
#     'Engineer',
#     'Analyst',
#     'Assistant',
#
# ]
#
# # job_titles = df['Job title']
#
# vectorizer = TfidfVectorizer(stop_words='english')
#
# X = vectorizer.fit_transform(job_titles)
#
# K = 20
#
# kmeans = KMeans(n_clusters=K, random_state=42, n_init='auto')
#
# kmeans.fit(X)
#
# clusters = kmeans.labels_
#
# for title, cluster in sorted(zip(job_titles, clusters), key=lambda x: x[1]):
#     print(f"'{title}' -> Cluster {cluster}")