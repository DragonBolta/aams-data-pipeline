from itertools import chain

import pyspark.sql.types as types
from pyspark.sql.functions import lit, create_map, udf, when, regexp_replace, trim, regexp_extract, initcap, upper, \
    year, try_to_timestamp, coalesce


@udf(returnType=types.StringType())
def standardize_us_state(val):
    if not val:
        return None
    try:
        import us
        state = us.states.lookup(str(val))
        return state.abbr if state else str(val).upper()
    except Exception:
        return str(val).upper()


@udf(returnType=types.StringType())
def convert_country(country_name):
    if not country_name:
        return None

    global _worker_cc
    if '_worker_cc' not in globals():
        import country_converter as coco
        _worker_cc = coco.CountryConverter()

    try:
        return _worker_cc.convert(names=country_name, to="ISO3", not_found=None)
    except Exception:
        return None

def clean(spark, df):
    df = df.withColumn('drop_reason', lit(None).astype(types.StringType()))

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
    df = df.withColumnsRenamed(rename_columns)

    df = df.withColumn('country', convert_country(df.country))

    df = df.withColumn('drop_reason', when(df.country.isNull(), 'Country Conversion Failed (ISO3=NaN)'))

    df = df.withColumn('education', when(df.education.isNull(), 'None'))

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

    yoe_mapping = create_map(*[lit(x) for x in chain(*yoe_bands.items())])

    for col in yoe_cols:
        df = df.withColumn(col, regexp_replace(df[col], " ", ""))
        df = df.withColumn(col, yoe_mapping.getItem(df[col]).cast(types.IntegerType()))
        # df = df.withColumn(col, when(column(col) == "", 0))
        df = df.withColumn('drop_reason', when(df[col].isNull(), f'Missing or Invalid {col} (dropna)').cast(types.StringType()))

    if 'response_timestamp' in df.columns:
        df = df.withColumn('response_timestamp', try_to_timestamp(df.response_timestamp, lit("M/d/yyyy H:m:s")))
        df = df.withColumn('year', year(df.response_timestamp).cast(types.IntegerType()))

        df = df.withColumn('drop_reason',
                           when(df.response_timestamp.isNull(), 'Missing or Invalid Timestamp/Year (dropna)'))

    else:
        df = df.withColumn('year', lit(None))

    text_cols = ['industry', 'job_title', 'city', 'currency', 'income_context', 'us_state']

    for col in text_cols:
        df = df.withColumn(col, trim(df[col]).cast(types.StringType()))
        # df = df.withColumn(col, when(df[col].isNull(), None))
        none_mappings = {
            'nan': None,
            'None': None,
            '': None
        }
        none_map_func = create_map(*[lit(x) for x in chain(*none_mappings.items())])
        df = df.withColumn(col, coalesce(none_map_func.getItem(df[col]), df[col]))

    df = df.withColumn('job_title', initcap(df.job_title))
    df = df.withColumn('city', initcap(df.city))
    df = df.withColumn('currency', upper(df.currency))

    money_cols = ['salary', 'bonus']
    for col in money_cols:
        df = df.withColumn(col, df[col].cast(types.StringType()))
        df = df.withColumn(col, regexp_replace(df[col], r'[$,]', '').cast(types.IntegerType()))

    df = df.withColumn('age', regexp_replace(df.age, "under 18", "17"))
    df = df.withColumn('age', regexp_extract(df.age, r'^(\d+)', 0))

    df = df.withColumn('us_state', standardize_us_state(df.us_state))

    bad_rows = df.where(~df.drop_reason.isNull())
    good_rows = df.where(df.drop_reason.isNull()).drop('drop_reason')

    return good_rows, bad_rows