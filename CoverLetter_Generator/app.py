import streamlit as st
import pandas as pd
import json
import utils
import os
import json

CSV_PATH = "./CoverLetter_Generator/app_data/jobs_saved.csv"

def show_skills_lists(tech_stack, soft_skills):
    # Create two columns for displaying the lists side by side
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Tech Stack")
        show_word_list(tech_stack)

    with col2:
        st.header("Soft Skills")
        show_word_list(soft_skills)

# Helper function to display a list of words
def show_word_list(skill_data):
    # Convert the skill data to a list of tuples and sort it by frequency (optional)
    sorted_skills = sorted(skill_data.items(), key=lambda x: x[1], reverse=True)
    
    # Display each skill as a list item
    for skill, _ in sorted_skills:
        st.write(f"- {skill}")

# Load job offers from CSV
def load_job_offers():
    if 'df' in st.session_state:
        return st.session_state.df
    else:
        try:
            return pd.read_csv('job_offers.csv')
        except FileNotFoundError:
            return pd.DataFrame(columns=["Company", "Role", "Tech Stack", "Soft Skills", "Raw offer"])

def show_offer_selection_and_cover_letter():
    # Load the job offers
    job_offers_df = load_job_offers()

    # Create a dropdown menu to select a job offer
    if not job_offers_df.empty:
        # Create a list of options for the dropdown menu
        job_offer_options = [
            f"{row['Role']} -- {row['Company']}" for _, row in job_offers_df.iterrows()
        ]
        
        selected_offer_text = st.selectbox("Select Job Offer", job_offer_options)

        if selected_offer_text:
            # Extract the role and company from the selected offer text
            role, company = selected_offer_text.split(' -- ')

            # Find the selected offer in the DataFrame
            selected_offer = job_offers_df[
                (job_offers_df["Role"] == role) & 
                (job_offers_df["Company"] == company)
            ].iloc[0]

            
            # Button to generate cover letter
            if st.button("Generate Cover Letter"):
                cover_letter = utils.generate_cover_letter(selected_offer, api_key=api_key)
                st.text_area("Cover Letter", cover_letter, height=300)
    else:
        st.write("No job offers available. Please submit a job offer first.")

### STREAMLIT APP ###

# Set page title
st.set_page_config(page_title="Job Search Tools", layout="wide")

# Title
st.title("Job Search Tools")

# Ensure API key is set
api_key = os.getenv("OPENAI_TEST_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize session state to store the dataframe
if 'df' not in st.session_state:
    # Create initial dataframe with dummy data 
    st.session_state.df = pd.read_csv(CSV_PATH)

# Text area for raw job offer input
job_offer_input = st.text_area("Enter the raw job offer here:", height=150)

# Submit button for job offer
if st.button("Submit Job Offer"):
    if job_offer_input:
        processed_job_offer = utils.extract_job_requirements(job_description=job_offer_input, api_key=api_key)
        
        # Add new row with the submitted job offer
        new_row = pd.DataFrame({
            "Company": [processed_job_offer["company"]],
            "Role": [processed_job_offer["role"]],
            "Tech Stack": [json.dumps(processed_job_offer["tech_stack"])],
            "Soft Skills": [json.dumps(processed_job_offer["soft_skills"])],
            "Raw offer": [job_offer_input],
        })
        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        # Save DataFrame to CSV file
        st.session_state.df.to_csv(CSV_PATH, index=False)
        st.success("Job offer submitted successfully!")
    else:
        st.warning("Please enter a job offer before submitting.")

# Display the current dataframe with plots and optional raw offer details
st.write("Current Job Search Data:")

for index, row in st.session_state.df.iterrows():
    with st.expander(f"{row['Company']} - {row['Role']}", expanded=True):
        st.write(f"Company: {row['Company']}")
        st.write(f"Role: {row['Role']}")
        
        # Display skills graphs by default
        tech_stack = json.loads(row['Tech Stack'])
        soft_skills = json.loads(row['Soft Skills'])
        show_skills_lists(tech_stack, soft_skills)
        
        # Button to show/hide raw offer details
        if st.button(f"Show/Hide Raw Offer Details", key=f"btn_{index}"):
            st.text_area("Raw offer details:", value=row['Raw offer'], height=150, key=f"raw_{index}")

show_offer_selection_and_cover_letter()