import pandas as pd
import streamlit as st
import io
import os
from urllib.parse import quote_plus

dbuser,dbpass,dbhost,dbport = os.getenv('dbuser'),quote_plus(os.getenv('dbpass')),os.getenv('dbhost'),os.getenv('dbport')
connection_string = f'mysql+pymysql://{dbuser}:{dbpass}@{dbhost}:{dbport}/housing'

def get_ready_test(RESULTS_PATH: str, uploaded_file):
    """
    Prepare the test DataFrame by validating the uploaded file and renaming its columns.
    
    Args:
        RESULTS_PATH (str): Path to the results file.
        uploaded_file: Streamlit uploaded file object.
    
    Returns:
        pd.DataFrame: Prepared test DataFrame.
    """
    results = pd.read_csv(RESULTS_PATH)
    results.columns = ['id', 'real']

    test = pd.read_csv(io.StringIO(uploaded_file.read().decode('utf-8')))

    if test.columns.to_list() != ['Id', 'Expensive']:
        st.error('Column names must match "Id" and "Expensive" - case sensitive!')
        return 0
    if test.shape != (1459, 2):
        st.error('Your file should contain 1459 rows and 2 columns')
        return 0
    if test.Expensive.unique().tolist() not in [[0, 1], [1, 0], [1], [0]]:
        st.error('Predictions should only have values of 0 and 1')
        return 0
    if (test.Id == results.id).sum() != 1459:
        st.error("Your Id column might be wrong or mixed up. You should have same Id's as the test file. Order of Id's should also be the same.")
        return 0

    test.columns = ['id', 'preds']
    return test.assign(
        id=lambda df_: df_['id'].astype('int32'),
        preds=lambda df_: df_['preds'].astype('object'),
    )


def get_accuracy(RESULTS_PATH: str, test: pd.DataFrame):
    """
    Calculate the accuracy of the test predictions and return a DataFrame with participant results.
    
    Args:
        RESULTS_PATH (str): Path to the results file.
        test (pd.DataFrame): Test DataFrame.
    
    Returns:
        pd.DataFrame: DataFrame with participant results.
    """
    results = pd.read_csv(RESULTS_PATH)
    results.columns = ['id', 'real']

    return (
        results
            .assign(
                id=lambda df_: df_['id'].astype('int32'),
                real=lambda df_: df_['real'].astype('object')
            )
            .merge(test, how='left', on='id')
            .assign(check=lambda df_: df_['real'] == df_['preds'])
            .agg({'check': ['sum']})
            .assign(
                accuracy=lambda df_: df_['check'] / results.shape[0],
                participant=st.session_state.text_input,
                submission_time=pd.Timestamp.now()
            )
            .astype({'accuracy': 'float64'})
            .filter(['participant', 'accuracy', 'submission_time'])
    )



def plot_submissions(participant_name):
    """
    Plot submission accuracy for a participant over time.
    
    Args:
        participant_name (str): Name of the participant.
    """
    participant_submissions = (
        pd.read_sql("submissions",con=connection_string)
            .query('participant == @participant_name')
            .filter(['submission_time', 'accuracy'])
            .set_index('submission_time')
            .copy()
    )
    if len(participant_submissions) > 1:
        st.line_chart(participant_submissions)
    else:
        st.success('Congratulations on your first submission!')
    

def update_submissions(participant_results: pd.DataFrame):
    """
    Update the submissions file with the participant's results.

    Args:
        participant_results (pd.DataFrame): DataFrame containing the participant's results.
    """
    submissions_df = get_submissions_dataframe()
    updated_submissions_df = pd.concat([submissions_df, participant_results])
    #updated_submissions_df.to_pickle('files_to_update/submissions.pkl')
    updated_submissions_df.to_sql("submissions",con=connection_string,if_exists='append', index=False)


def show_leaderboard(): 
    st.title('LEADERBOARD')
    
    submissions_df = get_submissions_dataframe()
    if not submissions_df.empty:
        leaderboard_df = generate_leaderboard_dataframe(submissions_df)
        st.dataframe(leaderboard_df)
    else:
        st.write("There is no submission.")


def get_submissions_dataframe():
    try:
        return pd.read_sql("submissions",con=connection_string) #pd.read_pickle('files_to_update/submissions.pkl')
    except FileNotFoundError:
        return pd.DataFrame(columns=['participant', 'accuracy', 'submission_time'])


def generate_leaderboard_dataframe(submissions_df):
    best_results_per_participant = (
        submissions_df
        .assign(
            attempts=lambda df_: df_.groupby('participant')['participant'].transform('count')
        )
        .sort_values(['accuracy','submission_time'], ascending=[False, True])
        .drop_duplicates(subset=['participant'], keep='first')
        .assign(position=lambda df_: range(1, len(df_) + 1))
        .set_index('position')
        .filter(['participant', 'accuracy', 'attempts'])
        )

    return best_results_per_participant


def update_submissions(participant_results: pd.DataFrame):
    submissions_df = get_submissions_dataframe()
    updated_submissions_df = pd.concat([submissions_df, participant_results])
    #updated_submissions_df.to_pickle('files_to_update/submissions.pkl')
    updated_submissions_df.to_sql("submissions",con=connection_string,if_exists='append', index=False)
