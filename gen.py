import streamlit as st
import google.generativeai as model
import dotenv
import os
from hashlib import sha256
from pymongo import MongoClient
from datetime import datetime
import logging
from fpdf import FPDF
import pyttsx3

# Load environment variables
dotenv.load_dotenv()
api_key = os.getenv("api_key")
model.configure(api_key=api_key)
gen1 = model.GenerativeModel(model_name="gemini-pro")

# Set up logging
logging.basicConfig(filename='techiehelp_chatbot.log', level=logging.INFO)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")  # Use your MongoDB URI
db = client["mongodb"]  # Replace with your database name
users_collection = db["users"]  # For storing user credentials
chat_collection = db["chat_history"]  # For storing chat history

# Helper functions for MongoDB
def store_message(query, response):
    message = {
        "query": query,
        "response": response,
        "timestamp": datetime.now()
    }
    chat_collection.insert_one(message)

def fetch_chat_history():
    messages = chat_collection.find().sort("timestamp", -1)  # Sorting by timestamp in descending order
    return [{"query": msg["query"], "response": msg["response"], "timestamp": msg["timestamp"]} for msg in messages]

def store_user(username, email, password):
    hashed_password = sha256(password.encode()).hexdigest()
    users_collection.insert_one({"username": username, "email": email, "password": hashed_password})

def validate_user(email, password):
    hashed_password = sha256(password.encode()).hexdigest()
    user = users_collection.find_one({"email": email, "password": hashed_password})
    return user

def update_password(email, new_password):
    hashed_password = sha256(new_password.encode()).hexdigest()
    users_collection.update_one({"email": email}, {"$set": {"password": hashed_password}})

# Logging function for interactions
def log_interaction(query, response):
    logging.info(f"Time: {datetime.now()}, User Query: {query}, AI Response: {response}")

import difflib

def techiehelp_responses(user_query):
    # Define FAQ responses
    faq_responses = {
        "who is the founder of techiehelp": (
            "TechieHelp was founded by Amit Kumar, a front-end developer and AI enthusiast. "
            "Visit our website for more. Contact us via email for more information. "
            "Email: amitk25783@gmail.com & LinkedIn: https://www.linkedin.com/in/amit-kumar-686196225/"
        ),
        "what is techiehelp": (
            "TechieHelp is a dynamic platform designed to empower students and professionals by providing a range of services like Web Development, "
            "App Development, SEO, UI/UX Design, and Admissions Support. Visit our website: https://techiehelpt.netlify.app/"
        ),
        "how can i join techiehelp": "You can join TechieHelp by signing up on our website or contacting us via email.",
        "what services does techiehelp offer": (
            "TechieHelp offers services like Web Development, App Development, SEO, UI/UX Design, Admissions Support, and Internships."
        ),
        "how can i contact techiehelp": "You can contact us via our email address or through the contact form on our website.",
        "does techiehelp provide internships": "Yes, TechieHelp provides internships in various domains. Visit our website for more details.",
        "what is the vision of techiehelp": "Our vision is to empower individuals with knowledge, skills, and opportunities in technology and beyond.",
        "how can i apply for an internship at techiehelp": "Visit the internships section on our website and apply through the provided form.",
        "does techiehelp have a mobile app": "Currently, we are working on a mobile app to make our services more accessible.",
        "what technologies does techiehelp use": (
            "TechieHelp uses modern technologies like React, Python, Machine Learning, Flask, and more to deliver top-notch solutions."
        ),
        "can techiehelp help with admissions": "Yes, TechieHelp provides admissions support for students seeking guidance.",
        "does techiehelp provide certificates": "Yes, we provide certificates for internships and workshops conducted by TechieHelp.",
        "what are the benefits of joining techiehelp": (
            "By joining TechieHelp, you gain access to internships, skill development programs, mentorship, and project opportunities."
        ),
        "how can i contribute to techiehelp": "You can contribute by collaborating on projects, volunteering, or joining as a mentor.",
        "does techiehelp host workshops": "Yes, TechieHelp regularly hosts workshops on various topics, including AI and Web Development.",
        "how do i stay updated with techiehelp": "Follow us on our social media platforms or subscribe to our newsletter.",
        "is techiehelp free": (
            "TechieHelp offers both free and premium services. Check our website for more details on pricing and plans."
        ),
        "can techiehelp help with website design": "Yes, we specialize in creating professional and responsive website designs.",
        "what is techiehelp's chatbot": (
            "TechieHelp's chatbot is an AI assistant designed to answer your questions and provide information about our services."
        ),
        "how can i donate to techiehelp": "Contact us via email to discuss donation options.",
        "does techiehelp have a physical office": "We currently operate online but are planning to expand to physical locations.",
        "what industries does techiehelp serve": "We cater to various industries, including education, technology, and startups.",
        "can techiehelp help with social media marketing": "Yes, we provide social media marketing services to boost your online presence.",
        "does techiehelp offer free trials": "We offer free trials for some of our services. Contact us for more details.",
        "how do i cancel my techiehelp subscription": "You can cancel your subscription via your account settings on our website.",
        "can techiehelp help with content writing": "Yes, we offer content writing services for blogs, websites, and more.",
        "does techiehelp provide job placements": "We assist with job placements through our network of partners and clients.",
        "what programming languages does techiehelp teach": (
            "We teach programming languages like Python, JavaScript, Java, and more through our courses and workshops."
        ),
        "techiehelp internship : how to apply": "Visit the internships section on our website and apply through the provided form. Apply Now : https://techiehelpt.netlify.app/intern",
        "techiehelp internship : duration": "The duration of internships at TechieHelp varies based on the project and requirements.",
        "techiehelp internship : eligibility": "Internship eligibility criteria include technical skills, communication, and a willingness to learn.",
        "techiehelp internship : benefits": "Interns at TechieHelp gain hands-on experience, mentorship, and networking opportunities.",
        "techiehelp internship : selection process": (
            "The selection process for internships includes an application review and interview. "
            "Apply now for internship. Link: https://techiehelpt.netlify.app/intern"
        ),
        "techiehelp services : web development": "TechieHelp offers professional web development services for businesses and individuals.",
        "techiehelp services : app development": "We specialize in creating custom mobile applications for Android and iOS platforms.",
        "techiehelp services : seo": "Our SEO services help improve your website's search engine ranking and online visibility.",
        "techiehelp services : ui/ux design": "We provide UI/UX design services to create engaging and user-friendly interfaces.",
        "techiehelp services : admissions support": "Our admissions support services help students secure admissions to top institutions.",
        "techiehelp services : internships": "We offer internships in various domains to help students gain practical experience.",
        "techiehelp services : certificates": "TechieHelp provides certificates for internships and workshops conducted by us.",
        "techiehelp services : mentorship": "Our mentorship programs connect students with industry experts for guidance and support.",
        "techiehelp services : workshops": "We conduct workshops on topics like AI, Web Development, and more to enhance your skills.",
        "techiehelp services : social media marketing": "Our social media marketing services help businesses grow their online presence.",
        "techiehelp services : content writing": "We offer professional content writing services for websites, blogs, and more.",
    }

    # Normalize user query for matching
    normalized_query = user_query.lower()

    # Attempt exact match
    if normalized_query in faq_responses:
        return faq_responses[normalized_query]

    # Attempt fuzzy matching for close matches
    close_matches = difflib.get_close_matches(normalized_query, faq_responses.keys(), n=1, cutoff=0.6)
    if close_matches:
        return faq_responses[close_matches[0]]

    # Fallback to AI model for unmatched queries
    return fallback_to_ai(user_query)

def fallback_to_ai(query):
    # Call to AI model (e.g., Gemini API)
    response = gen1.generate_content(("you are a friendly model", query)).text
    return response


# Text-to-Speech Conversion
def convert_to_audio(response_text):
    engine = pyttsx3.init()
    engine.save_to_file(response_text, 'response.mp3')
    engine.runAndWait()
    return 'response.mp3'

# PDF Generation
def generate_pdf(response_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, response_text)
    pdf_file = "response.pdf"
    pdf.output(pdf_file)
    return pdf_file

# Streamlit interface
st.title("TechieHelp-AI Chatbot Assistant")
st.image("logo.png", width=150)

# Check if user is logged in
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""  # Initialize username in session_state

# Login and Signup Section
if not st.session_state.logged_in:
    login_mode = st.radio("Select an option", ["Login", "Signup"])
    
    if login_mode == "Signup":
        st.subheader("Create a new account")
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if password == confirm_password:
            if st.button("Sign Up"):
                if not users_collection.find_one({"email": email}):
                    store_user(username, email, password)
                    st.success("Account created successfully. Please log in.")
                else:
                    st.error("User already exists.")
        else:
            st.error("Passwords do not match.")
    
    elif login_mode == "Login":
        st.subheader("Login to your account")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            user = validate_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.username = user["username"]
                st.success("Login successful!")
            else:
                st.error("Invalid credentials.")

# Dashboard and Features for Logged-in Users
if st.session_state.logged_in:
    st.sidebar.header(f"Welcome, {st.session_state.username}!")
    
    # Sidebar navigation
    section = st.sidebar.radio("Navigation", ["Dashboard", "Chatbot", "Change Password", "History", "Logout"])
    
    if section == "Dashboard":
        st.header("User Dashboard")
        st.write("Welcome to your dashboard! Here you can manage your account and view recent activity.")
        st.write(f"Email: {st.session_state.user_email}")
    
    elif section == "Chatbot":
        st.header("TechieHelp Chatbot")
        user_query = st.text_input("Ask me anything about TechieHelp!")
        if user_query:
            ai_response = techiehelp_responses(user_query)
            st.write(ai_response)

            # Convert to audio
            audio_file = convert_to_audio(ai_response)
            st.audio(audio_file)

            # Download as PDF
            pdf_file = generate_pdf(ai_response)
            with open(pdf_file, "rb") as f:
                st.download_button("Download as PDF", f, file_name="response.pdf")
            
            store_message(user_query, ai_response)
    
    elif section == "Change Password":
        st.header("Change Password")
        old_password = st.text_input("Old Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        
        if st.button("Update Password"):
            user = validate_user(st.session_state.user_email, old_password)
            if user:
                if new_password == confirm_new_password:
                    update_password(st.session_state.user_email, new_password)
                    st.success("Password updated successfully!")
                else:
                    st.error("New passwords do not match.")
            else:
                st.error("Old password is incorrect.")
    
    elif section == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.experimental_rerun()

    # History Section with Toggle for Answer Visibility
    if section == "History":
        st.header("Chat History")
        history = fetch_chat_history()
        if history:
            for idx, msg in enumerate(history):
                question = msg["query"]
                answer = msg["response"]
                # Use the index (or any other unique identifier) as a key
                if st.button(f"Question: {question}", key=f"question_{idx}"):
                    # Toggle visibility of the answer
                    if st.session_state.get(f"show_answer_{idx}", False):
                        st.write(f"Answer: {answer}")
                        st.session_state[f"show_answer_{idx}"] = False  # Hide answer next time
                    else:
                        st.session_state[f"show_answer_{idx}"] = True  # Show answer next time
                else:
                    if st.session_state.get(f"show_answer_{idx}", False):
                        st.write(f"Answer: {answer}")
        else:
            st.write("No chat history available.")
