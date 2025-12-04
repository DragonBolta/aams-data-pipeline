import pandas as pd
import country_converter as coco
import us


def standardize_us_state(val):
    if not val:
        return None
    state = us.states.lookup(str(val))
    return state.abbr if state else val.upper()


def clean(df):
    dropped_dataframes_list = []

    rename_columns = {
        "How old are you?": "age",
        "What industry do you work in?": "industry",
        "Job title": "job_title",
        "If your job title needs additional context, please clarify here:": "job_context",
        "What is your annual salary? (You'll indicate the currency in a later question. If you are part-time or hourly, please enter an annualized equivalent -- what you would earn if you worked the job 40 hours a week, 52 weeks a year.)": "salary",
        "How much additional monetary compensation do you get, if any (for example, bonuses or overtime in an average year)? Please only include monetary compensation here, not the value of benefits.": "bonus",
        "Please indicate the currency": "currency",
        "If your income needs additional context, please provide it here:": "income_context",
        "What country do you work in?": "country",
        "If you're in the U.S., what state do you work in?": "us_state",
        "What city do you work in?": "city",
        "How many years of professional work experience do you have overall?": "professional_yoe",
        "How many years of professional work experience do you have in your field?": "industry_yoe",
        "What is your highest level of education completed?": "education",
        "What is your race? (Choose all that apply.)": "race",
        'What is your gender?': "gender"
    }
    df = df.rename(columns=rename_columns)

    text_cols = ['industry', 'job_title', 'city', 'currency', 'income_context', 'country', 'us_state']

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

    yoe_cols = ['professional_yoe', 'industry_yoe']
    yoe_bands = {
        '1 year or less': 0,
        '2 - 4 years': 2,
        '5 - 7 years': 5,
        '8 - 10 years': 8,
        '11 - 20 years': 11,
        '21 - 30 years': 21
    }

    for col in yoe_cols:
        df[col] = df[col].map(yoe_bands)

        index_before = df.index
        df_after = df.dropna(subset=[col])
        index_after = df_after.index

        dropped_indices = index_before.difference(index_after)
        if not dropped_indices.empty:
            dropped_df = df.loc[dropped_indices].copy()
            dropped_df['drop_reason'] = f'Missing or Invalid {col} (dropna)'
            dropped_dataframes_list.append(dropped_df)

        df = df_after
        df[col] = df[col].astype(int)

    index_before = df.index
    df_after = df.dropna(subset=["education"])
    index_after = df_after.index

    dropped_indices = index_before.difference(index_after)
    if not dropped_indices.empty:
        dropped_df = df.loc[dropped_indices].copy()
        dropped_df['drop_reason'] = 'Missing Education (dropna)'
        dropped_dataframes_list.append(dropped_df)

    df = df_after

    cc = coco.CountryConverter()

    index_before = df.index
    df['country'] = cc.pandas_convert(series=df['country'], to='ISO3', not_found=None)
    df_after = df.dropna(subset=['country'])
    index_after = df_after.index

    dropped_indices = index_before.difference(index_after)
    if not dropped_indices.empty:
        dropped_df = df.loc[dropped_indices].copy()
        dropped_df['drop_reason'] = 'Country Conversion Failed (ISO3=None)'
        dropped_dataframes_list.append(dropped_df)

    df = df_after

    index_before = df.index
    df_after = df[df['country'].astype(str).str.match(r'^[A-Z]{3}$')]
    index_after = df_after.index

    dropped_indices = index_before.difference(index_after)
    if not dropped_indices.empty:
        dropped_df = df.loc[dropped_indices].copy()
        dropped_df['drop_reason'] = 'Country Code Not ISO3 Format'
        dropped_dataframes_list.append(dropped_df)

    df = df_after

    df['us_state'] = df['us_state'].apply(standardize_us_state)

    if dropped_dataframes_list:
        final_dropped_df = pd.concat(dropped_dataframes_list)
    else:
        final_dropped_df = pd.DataFrame()

    df = df.reset_index(drop=True)

    return df, final_dropped_df