import pandas as pd
import country_converter as coco
import us  # <-- New library


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

    text_cols = ['industry', 'job_title', 'city', 'currency', 'us_state']

    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({'nan': None, 'None': None, '': None})

    df['job_title'] = df['job_title'].str.title()
    df['city'] = df['city'].str.title()
    df['currency'] = df['currency'].str.upper()

    money_cols = ['salary', 'bonus']
    for col in money_cols:
        df[col] = df[col].astype(str).str.replace(r'[$,]', '', regex=True)
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df['age'] = df['age'].replace("under 18", "17")
    df['age'] = df['age'].astype(str).str.extract(r'^(\d+)').fillna(0).astype(int)

    cc = coco.CountryConverter()

    df['country'] = cc.pandas_convert(series=df['country'], to='ISO3', not_found=None)
    df = df.dropna(subset=['country'])
    df = df[df['country'].astype(str).str.match(r'^[A-Z]{3}$')]

    def standardize_us_state(val):
        if not val:
            return None
        state = us.states.lookup(str(val))
        return state.abbr if state else val.upper()

    df['us_state'] = df['us_state'].apply(standardize_us_state)

    df = df.reset_index(drop=True)

    return df