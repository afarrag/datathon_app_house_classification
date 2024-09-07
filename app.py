import streamlit as st
import pandas as pd
from src.pd_functions import *
from src.utils import validate_csv_file
import base64
from streamlit.components.v1 import html
import random
import math
import os


# Constants
RESULTS_PATH = 'data/results_housing_class.csv'
from urllib.parse import quote_plus

dbuser,dbpass,dbhost,dbport = os.getenv('dbuser'),quote_plus(os.getenv('dbpass')),os.getenv('dbhost'),os.getenv('dbport')
connection_string = f'mysql+pymysql://{dbuser}:{dbpass}@{dbhost}:{dbport}/housing'

def main():
    st.title('Housing Classification App')
    st.write('Welcome to the housing classification app. Please enter your name and upload your results file to check your accuracy and see the leaderboard.')


    try:
        pd.read_pickle('files_to_update/submissions.pkl').to_sql("submissions",index=False, con=connection_string, if_exists='append')
    except: pass
    else:
        st.success('found pkl, copied to sql')
        os.remove('files_to_update/submissions.pkl')

    participant_name = get_participant_name()

    if participant_name:
        uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])

        if uploaded_file:
            if validate_csv_file(uploaded_file):
                process_uploaded_file(uploaded_file, participant_name)
            else:
                st.error('The uploaded file is not a valid CSV file. Please upload a valid CSV file.')
        else:
            st.warning('Please upload a file.')
    else:
        st.warning('Please enter a participant name.')

    display_leaderboard()

def get_participant_name():
    text_input_container = st.empty()
    participant_name = text_input_container.text_input(
        "Introduce participant name: ",
        key="text_input"
    )
    return participant_name

def process_uploaded_file(uploaded_file, participant_name):
    if validate_csv_file(uploaded_file):
        try:
            uploaded_file.seek(0)  # Reset file pointer to the beginning
            test = get_ready_test(RESULTS_PATH, uploaded_file)
            participant_results = get_accuracy(RESULTS_PATH, test)

            st.success('Dataframe uploaded successfully!')

            all_data = pd.read_sql("submissions",con=connection_string)
            
            #all_data=pd.read_pickle('files_to_update/submissions.pkl')
            if (participant_results.iloc[0,1]) > (all_data.accuracy.max()):
                autoplay_audio('static/claps.mp3')
                rain("great.png",math.floor(random.random()*100))
                
            else:
                autoplay_audio('static/success.mp3')
                rain("good.png",math.floor(random.random()*100))
            display_participant_results(participant_results)
            update_and_plot_submissions(participant_results, participant_name)

            if (participant_results.iloc[0,1]) > (all_data.accuracy.max()):
                with st.status("Sending to Slack..."):
                    send_msg_to_slack(participant_results.iloc[0,0],participant_results.iloc[0,1])
                st.success("Sent to Slack")
        except Exception as e:
            st.error(f'The file could not be processed. Error: {e}')
            st.exception(e)
    else:
        st.error('The file has a wrong format, please, review it and ensure it contains the required columns.')



def display_participant_results(participant_results):
    st.title('Participant results')
    st.dataframe(participant_results)

def update_and_plot_submissions(participant_results, participant_name):
    try:
        update_submissions(participant_results)
        plot_submissions(participant_name)
    except:
        #participant_results.to_pickle('files_to_update/submissions.pkl')
        participant_results.to_sql("submissions",con=connection_string,if_exists='append', index=False)

def display_leaderboard():
    try:
        show_leaderboard()
    except:
        st.write("There is no submission.")
      
def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )
def rain(photo,x):
    # Define your javascript
   
    my_css="""
    .rainPhoto {
  position: fixed;
  animation-duration: 20s;
  animation-name: slidedown;
  animation-fill-mode: forwards;
  width: 100px;
  top: 0;
  left: %dvw;
}

@keyframes slidedown {
  to {
    top: 120%%;
  }
}
    """ % (x)
    # Wrapt the javascript as html code
    my_html = f'<style>{my_css}</style><img class="rainPhoto" src="./app/static/{photo}"/>'
    st.write(my_html,unsafe_allow_html=True)
    
def send_msg_to_slack(new_top,new_score):
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    import time
    import os
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.core.os_manager import ChromeType
    ########################################################
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')

    # Slack credentials and channel URL
    SLACK_URL = os.getenv("SLACK_URL")
    EMAIL = os.getenv("EMAIL")
    PASSWORD = os.getenv("PASSWORD")
    CHANNEL_URL = os.getenv("CHANNEL_URL")
   
    # Initialize WebDriver (here using Chrome)
    driver = webdriver.Chrome(options=options, service=Service(
            ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
        ))
    driver.get(SLACK_URL)
    time.sleep(2)  # Adjust if necessary to allow time for page load

    from urllib.request import urlopen
    import pickle

    cookies = urlopen(os.getenv("cookies"))
    cookies = pickle.load(cookies)
    for cookie in cookies:
        driver.add_cookie(cookie)
    # Open Slack and login
    

    # Find and fill in email and password fields, then click login
    from selenium.webdriver.common.by import By

    email_input=driver.find_element(By.ID, 'email')
    email_input.send_keys(EMAIL)
    password_input=driver.find_element(By.ID, 'password')
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)
    time.sleep(5)  # Adjust if necessary to allow time for page load


    # Open Slack and login
    driver.get(CHANNEL_URL)
    time.sleep(2)  # Adjust if necessary to allow time for page load

    msg = f":rocket: :trophy: {new_top} is now #1 on the [LEADERBORD](https://datathon.streamlit.app) with score {new_score}!"

    message_box = driver.find_element(By.CLASS_NAME, 'ql-editor')
    message_box.send_keys(msg)
    message_box.send_keys(Keys.RETURN)




if __name__ == "__main__":
    main()
