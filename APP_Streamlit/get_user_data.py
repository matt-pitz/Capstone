import streamlit as st
import random
from datetime import datetime
import pandas as pd


def generate_random_user_id():
    """Generate a random user ID."""
    return f"user_{random.randint(1000, 9999)}"


def get_user_data():
    st.title("Runner Training Plan - User Input Form")

    # User Type
    user_type = st.radio("Are you a new user?", ('Yes', 'No'))
    new_user = True if user_type == 'Yes' else False

    user_id = None  # Initialize user_id variable to None
    missing_fields = []

    if new_user:
        # New User Info
        st.header("New User Information")
        
        age = st.number_input("What is your age?", min_value=18, step=1)
        gender = st.selectbox("What is your gender?", ('Male', 'Female'))
        distance_last_week = st.number_input("Distance run last week (in kilometers):", min_value=0.0, step=0.1)
        pace_last_week = st.time_input("Average pace last week:", value=datetime.strptime('00:00:00', '%H:%M:%S'))
        num_days_run_last_week = st.slider("Number of days run in last week:", 0, 7)
        days_since_last_run = st.slider("Days since last run:", 0, 30)

        # Generate a random user ID for new users
        user_id = generate_random_user_id()

        # Additional data collection for new users can be added here
    else:
        # Returning User Info
        st.header("Returning User Information")
        
        user_id = st.text_input("Please enter your user ID:")

        # Additional data collection for returning users can be added here
        if user_id:
            num_days_run_last_week = st.slider("Number of days run in last week:", 0, 7)
            days_since_last_run = st.slider("Days since last run:", 0, 30)

            # Check for missing fields for returning users
            if not num_days_run_last_week:
                missing_fields.append("Number of days run in last week")
            if not days_since_last_run:
                missing_fields.append("Days since last run")

    # Information on Each Run
    st.header("Information on Each Run")
    data = []
    for i in range(num_days_run_last_week):
        st.subheader(f"Day {i+1}")
        date = st.date_input("Enter a date you ran:", key=f"date_{i}")
        distance_value = st.number_input("How many kilometers did you run?", min_value=0.0, step=0.1, key=f"distance_{i}")
        pace_value = st.time_input("What was the total run pace?", key=f"pace_{i}")

        data.append([date, distance_value, pace_value])

    df = pd.DataFrame(data, columns=['Date', 'Distance (in km)', 'Pace'])

    # Validate inputs
    error_msg = ""
    if new_user:
        if not age or not gender or not distance_last_week or not pace_last_week or not num_days_run_last_week or not days_since_last_run:
            error_msg += "Please fill in all new user information fields.\n"
    else:
        if not user_id:
            error_msg += "Please enter your user ID for returning users.\n"

    if missing_fields:
        error_msg += f"Please fill in the following fields for returning users: {', '.join(missing_fields)}.\n"

    if error_msg:
        st.error("Errors found:\n" + error_msg)
        return None, None, None, None, None, None, None, None, None

    if new_user:
        return new_user, age, gender, distance_last_week, pace_last_week, num_days_run_last_week, days_since_last_run, df, user_id
    else:
        # Add a "Next" button for returning users if all fields are entered
        if st.button("Next"):
            return new_user, user_id, num_days_run_last_week, days_since_last_run, df
        else:
            return None, None, None, None, None, None, None, None, None
