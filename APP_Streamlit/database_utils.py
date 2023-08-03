import pandas as pd
from datetime import datetime
from datetime import timedelta
import pyarrow.parquet as pq

def load_data():
    '''function to load in datasets to memory'''

    # load in parquet data
    raw_df = pd.read_parquet('../App_Data/input_runners_all.parquet')

    # convert months to number
    def mtn(x):
        months = {
            'jan': 1,
            'feb': 2,
            'mar': 3,
            'apr': 4,
            'may': 5,
            'jun': 6,
            'jul': 7,
            'aug': 8,
            'sep': 9,
            'oct': 10,
            'nov': 11,
            'dec': 12
        }
        a = x.strip()[:3].lower()
        try:
            ez = months[a]
            return ez
        except:
            raise ValueError('Not a month')

    raw_df["current_month"] = raw_df["current_month"].apply(lambda x: mtn(x))

    # create user ID
    raw_df["user_id"] = raw_df["athlete"].astype(str) + "." + raw_df["current_month"].astype(str)

#     # Convert the "Duration" column to string in 'HH:MM:SS' format
    raw_df['Duration'] = raw_df['Duration'].astype(str)

    # remove any missings from the data
    raw_df = raw_df.dropna(subset=["prev_month_weekly_km"])

    return raw_df

    


def update_database(new_user, gender, age_bucket, month, weekly_target, number_of_days, user_id, updated_user_df):
    '''Update user database and return ratings'''

    if new_user and updated_user_df.empty:
        # cold start for new user. With no data. Assumes long run 2x distance other runs.
        new_user_data = {
            'user_id': [user_id] * 2,
            'run_distance_rounded': [round(weekly_target / 6), round(weekly_target / 3)],
            'weekly_frequency': [number_of_days - 1, 1]
        }
        update_user_db = pd.DataFrame(new_user_data)

    else:
        # load in new database
        user_df = pd.read_parquet('../App_Data/new_user_db.parquet')

        # align data types
        user_df['user_id'] = user_df['user_id'].astype('string')
        user_df['Date'] = pd.to_datetime(user_df['Date']).dt.date
        try:
            user_df['Duration'] = pd.to_datetime(user_df['Duration'])
            user_df['Duration'] = user_df['Duration'].apply(lambda x: x.strftime('%H:%M:%S'))
        except:
            pass
        

        # Check if 'Date' column is present in updated_user_df
        if 'Date' not in updated_user_df.columns:
            updated_user_df['Date'] = None

        try:
            updated_user_df['Duration'] = pd.to_timedelta(updated_user_df['Duration'])
        except:
            # Handle any invalid "Duration" values by setting them to NaT (Not-a-Time)
            updated_user_df['Duration'] = pd.to_timedelta(updated_user_df['Duration'], errors='coerce')


        # concatenate with updated data
        user_df = pd.concat([user_df, updated_user_df])

        # update user database
        user_df.to_parquet('../App_Data/new_user_db.parquet')

        # restrict to current user
        user_df = user_df[user_df['user_id'] == str(user_id)]

        # Find the most recent date in the time series
        most_recent_date = pd.to_datetime(user_df['Date']).max()

        # Calculate the date 30 days prior to the most recent date
        thirty_days_prior = most_recent_date - pd.Timedelta(days=30)

        # Select runs that are up to 30 days prior to the most recent date
        curr_month_runs = user_df[user_df['Date'] > thirty_days_prior]

        # create run ratings
        days_run = curr_month_runs['Date'].size

        curr_month_runs['run_distance_rounded'] = curr_month_runs.Distance.round()
        update_user_db = curr_month_runs.groupby(['run_distance_rounded'])['Distance'].agg('count').reset_index()
        update_user_db = update_user_db.rename(columns={'Distance': 'weekly_frequency'})
        update_user_db['weekly_frequency'] = update_user_db['weekly_frequency'] / (days_run / 7)
        update_user_db['user_id'] = user_id

    return update_user_db


def database_for_recommender(raw_df, new_user_df, gender, age_bucket, month, number_of_days, weekly_target):
    '''Filter raw data and add user data for the recommender system'''

    # Define objects for Surprise. Must be in user, item, rating order
    filtered_df = raw_df.loc[
        (raw_df['gender'] == gender) &
        (raw_df['age_bucket'] == age_bucket) &
        (raw_df['current_month'] == month) &
        (raw_df['prev_month_weekly_days_run'] > (number_of_days - 1)) & 
        (raw_df['prev_month_weekly_days_run'] < (number_of_days + 1)) &
        (raw_df['prev_month_weekly_km'] > weekly_target - 5) &
        (raw_df['prev_month_weekly_km'] < weekly_target + 5)
    ]

    if filtered_df.size <= 15:
        print("Insufficient data for", gender, age_bucket, target_kms)
        BREAK

    # Append new user data
    filtered_df = pd.concat([filtered_df, new_user_df])
    return filtered_df
