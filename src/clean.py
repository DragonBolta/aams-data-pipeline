import pandas as pd
import country_converter as coco
import us
import numpy as np


def standardize_us_state(val):
    if not val:
        return None
    state = us.states.lookup(str(val))
    return state.abbr if state else val.upper()


def clean(df):
    df = df.copy()
    df['drop_reason'] = np.nan
    df['drop_reason'] = df['drop_reason'].astype(object)

    rename_columns = {
        "Timestamp": "response_timestamp",
        "How old are you?": "age",
        "What industry do you work in?": "industry",
        "Job title": "job_title",
        "If your job title needs additional context, please clarify here:": "job_context",
        "What is your annual salary? (You'll indicate the currency in a later question. If you are part-time or hourly, please enter an annualized equivalent -- what you would earn if you worked the job 40 hours a week, 52 weeks a year.)": "salary",
        "How much additional monetary compensation do you get, if any (for example, bonuses or overtime in an average year)? Please only include monetary compensation here, not the value of benefits.": "bonus",
        "Please indicate the currency": "currency",
        "If \"Other,\" please indicate the currency here: ": "other_currency",
        "If your income needs additional context, please provide it here:": "income_context",
        "What country do you work in?": "country",
        "If you're in the U.S., what state do you work in?": "us_state",
        "What city do you work in?": "city",
        "How many years of professional work experience do you have overall?": "professional_yoe",
        "How many years of professional work experience do you have in your field?": "industry_yoe",
        "What is your highest level of education completed?": "education",
        'What is your race? (Choose all that apply.)': "race",
        'What is your gender?': "gender"
    }
    df = df.rename(columns=rename_columns)

    cc = coco.CountryConverter()
    df['country'] = cc.pandas_convert(series=df['country'], to='ISO3', not_found=np.nan)[0]

    country_fail_mask = df['country'].isna()
    df.loc[country_fail_mask & df['drop_reason'].isna(), 'drop_reason'] = 'Country Conversion Failed (ISO3=NaN)'

    education_fail_mask = df['education'].isna()
    df.loc[education_fail_mask, 'education'] = 'None'

    yoe_cols = ['professional_yoe', 'industry_yoe']
    yoe_bands = {
        '': 0,
        '1yearorless': 0,
        '2-4years': 2,
        '5-7years': 5,
        '8-10years': 8,
        '11-20years': 11,
        '21-30years': 21,
        '31-40years': 31,
        '41yearsormore': 41
    }

    for col in yoe_cols:
        original_values = df[col].copy()
        df[col] = original_values.str.replace(" ", "").map(yoe_bands)

        yoe_fail_mask = df[col].isna() & original_values.notna()

        df.loc[yoe_fail_mask & df['drop_reason'].isna(), 'drop_reason'] = f'Missing or Invalid {col} (dropna)'

    df['professional_yoe'] = df['professional_yoe'].astype('Int64')
    df['industry_yoe'] = df['industry_yoe'].astype('Int64')

    if 'response_timestamp' in df.columns:
        df['response_timestamp'] = pd.to_datetime(df['response_timestamp'], errors='coerce')
        df['year'] = df['response_timestamp'].dt.year
        df['year'] = df['year'].astype('Int64')

        timestamp_fail_mask = df['response_timestamp'].isna()
        df.loc[timestamp_fail_mask & df[
            'drop_reason'].isna(), 'drop_reason'] = 'Missing or Invalid Timestamp/Year (dropna)'

    else:
        df['year'] = pd.Series([pd.NA] * len(df), dtype="Int64")

    text_cols = ['industry', 'job_title', 'city', 'currency', 'income_context', 'us_state']

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

    df['us_state'] = df['us_state'].apply(standardize_us_state)

    bad_rows = df[df['drop_reason'].notna()].copy()
    good_rows = df[df['drop_reason'].isna()].copy()

    good_rows = good_rows.drop(columns=['drop_reason'])

    good_rows = good_rows.reset_index(drop=True)

    return good_rows, bad_rows