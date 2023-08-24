import streamlit as st
import pandas as pd
from src.pd_functions import *
from src.utils import validate_csv_file
import base64
from streamlit.components.v1 import html

# Constants
RESULTS_PATH = 'data/results_housing_class.csv'
html='''
<audio id="celebrate_audio" preload>  
  <source src="./app/static/claps.mp3" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>
<audio id="result_added" preload>  
  <source src="./app/static/success.mp3" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>
'''
def main():
    st.title('Housing Classification App')
    st.markdown(html,unsafe_allow_html=True)
    st.write('Welcome to the housing classification app. Please enter your name and upload your results file to check your accuracy and see the leaderboard.')

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
            all_data=pd.read_pickle('files_to_update/submissions.pkl')
            if (participant_results.iloc[0,1]) > (all_data.accuracy.max()):
                autoplay_audio('static/claps.mp3')
            else:
                autoplay_audio('static/success.mp3')
                rain()
            display_participant_results(participant_results)
            update_and_plot_submissions(participant_results, participant_name)
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
        participant_results.to_pickle('files_to_update/submissions.pkl')

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
  def rain():
    # Define your javascript
    my_js = """
    var rainDiv = document.querySelector('#action');
function appendImage() {
  var img = document.createElement('img');
  img.setAttribute('src', 'http://pixelartmaker.com/art/3ba7f5717ac3c63.png');
  img.style.left = Math.floor(Math.random() * 100) + 'vw';
  rainDiv.appendChild(img);}
  appendImage();
    """
    my_css="""
    img {
  position: fixed;
  animation-duration: 20s;
  animation-name: slidedown;
  animation-fill-mode: forwards;
  height: 100px;
  width: 100px;
  top: 0;
}

@keyframes slidedown {
  to {
    top: 120%;
  }
}
    """
    # Wrapt the javascript as html code
    my_html = f"<style>{my_css}</style><script>{my_js}</script>"
    
    # Execute your app
    st.title("Javascript example")
    html(my_html)

if __name__ == "__main__":
    main()
