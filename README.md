Customer Retention Project

Overview:

Welcome to the Customer Retention Project! This project is designed to help businesses predict and mitigate customer churn effectively. It consists of two main services: Churn Prediction Service and Language Model Service, all seamlessly integrated with a user-friendly Streamlit UI.


Churn Prediction Service:

The Churn Prediction Service utilizes a linear regression model to forecast customer churn. It is deployed using Flask inside a Docker container, ensuring scalability and ease of deployment. This service aids in identifying potential churn risks, allowing them to take proactive measures to retain valuable customers.

Deployment:

To deploy the Churn Prediction Service, follow these steps:

1. Install Docker on your system.
2. Build the Docker image using the provided Dockerfile.
3. Run the Docker container, exposing the necessary ports.

Language Model Service:

The Language Model Service is dedicated to generating personalized promotion emails for customers. It includes three sub-services:

Mail Generation Service: Creates initial drafts for promotion emails based on customer profiles and preferences. The mail generation service employs a Language Model (LLM) trained for this purpose. Due to resource constraints, the LLM model is deployed through LangChain, an integration that leverages OpenAI's models for mail generation.

Mail Revamping Service: Enhances the generated drafts by incorporating feedback and suggestions, ensuring a more engaging and effective email content.

Chat Bot for Content Brainstorming: Assists marketing teams in brainstorming content ideas for promotional emails. The Chat Bot leverages natural language processing to provide creative suggestions.


Streamlit UI

The Streamlit UI provides a cohesive interface for managing both the Churn Prediction and Language Model Services. It allows users to:

1. Access churn predictions service.
2. Generate and review promotion emails.
3. Engage with the Chat Bot to brainstorm content ideas for emails.


Deployment Process:

Churn Prediction Service:

Build the Image

Navigate to the Churn Prediction Service deployment directory:

cd Churn_Service/deployment

Build the Docker image:

docker build -t churn_prediction:1 .

Running the Service

Run the Docker container, mapping the models directory and exposing the necessary ports:

docker run -it -v "${PWD}/Churn_Service/models/:/home/models" -p 5050:9696 churn_prediction:1

Now, you can start the Streamlit UI to interact with the Churn Prediction Service:

streamlit run customer_service.py
