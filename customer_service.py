import streamlit as st

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

from Churn_Service.scripts.utils_and_constants import PREDICTION_URL
from Churn_Service.scripts.service import predict_churn
from LLM_Service.scripts.constant import API_KEY, COMPLETION_MODEL_NAME
from LLM_Service.scripts.service import mail_generation, mail_revamp, chat_mode


chatllm = ChatOpenAI(temperature=0.5, openai_api_key=API_KEY)
model = OpenAI(model=COMPLETION_MODEL_NAME, temperature=0.5, openai_api_key=API_KEY)


def revamp(mail=None):

    if mail is None:
        st.write(mail)
        mail = st.text_input("Enter the mail to be revamped")

    revamp_details = st.text_input("Enter corrections to be made")

    if st.button("Revamp"):
        if mail and revamp_details:
            mail = mail_revamp(model, mail, revamp_details)
            st.write(mail)
            return mail
        else:
            st.warning("Give the required information")


def churn_prediction():

    st.subheader("Predict the likelihood of customer churn with advanced analytics.")
    uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
    if uploaded_file:
        churn = predict_churn(PREDICTION_URL, uploaded_file)
        csv_data = churn.to_csv(index=False)  # Convert DataFrame to CSV string
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="my_data.csv",
            mime="text/csv",
        )


def generate_emails():
    st.subheader("Generate promotional emails using pre-existing")
    context = st.text_input("Enter mail context")

    if st.button("Generate"):
        if context:
            mail = mail_generation(model, context)
            st.write(mail)
            print(mail)
            return mail
        else:
            st.warning("Please enter a mail context before generating.")


def page1():
    st.title("Customer Retention Service")
    st.write(
        """Welcome to our Customer Retention Service. This service specializes in predicting the\
             likelihood of customer churn for a telecommunications company. Additionally, it generates \
            promotional emails tailored to individual customer contexts, enhancing targeted engagement."""
    )

    st.write(
        """This service offers diverse usage options:\n 1. Generate promotional emails using pre-existing\
              contexts.\n 2. Engage with the chatbot to gather insights and create contexts for personalized promotional\
              emails.\n 3. Predict the likelihood of customer churn with advanced analytics."""
    )


def page2():
    st.title("Generate promotional emails using pre-existing")
    st.write("Welcome to the Mail Generation Service")
    generate_emails()


def page3():
    st.title(
        "Engage with the chatbot to gather insights and create contexts for personalized promotional emails."
    )
    st.write("Welcome to the Chatbot Service")
    chat_mode(chatllm)


def page4():
    st.title("Predict the likelihood of customer churn with advanced analytics.")
    st.write("Welcome to the Churn Prediction Service")
    churn_prediction()


def page5():
    st.title("Revamp Your Mail")
    st.write("Welcome to the Mail Revamp Service")
    revamp()


def main():
    st.sidebar.title("Navigation")
    page_options = ["Home", "Generate Mail", "Chatbot", "Predict Churn", "Revamp Mail"]
    selected_page = st.sidebar.radio("Select a service", page_options)

    if selected_page == "Home":
        page1()
    if selected_page == "Generate Mail":
        page2()
    elif selected_page == "Chatbot":
        page3()
    elif selected_page == "Predict Churn":
        page4()
    elif selected_page == "Revamp Mail":
        page5()


# Run the Streamlit app
if __name__ == "__main__":
    main()
