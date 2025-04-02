import streamlit as st
from parse import parse_with_gemini
from scrape import scrape_website, split_dom_content, clean_body_content, extract_body_content
from datetime import datetime

API_URL = "https://m29oncz02i.execute-api.us-east-1.amazonaws.com/prod/"

st.title("AI Web Scraper")

# Check if the URL is already in session state, if not initialize it
if 'url' not in st.session_state:
    st.session_state.url = ""

# Input for the website URL
st.session_state.url = st.text_input("Enter a Website URL:", value=st.session_state.url)

# Check if the "Scrape Site" button is clicked
if st.button("Scrape Site"):
    st.write("Scraping the website...")
    
    # Scrape the website and process the content
    cleaned_content = scrape_website(st.session_state.url)
    # body_content = extract_body_content(result)
    # cleaned_content = clean_body_content(body_content)

    # Store the scraped content in session state
    st.session_state.dom_content = cleaned_content

    # Display cleaned content
    with st.expander("View DOM Content"):
        st.text_area("DOM Content", st.session_state.dom_content, height=300)

    # Store the scraped content to DynamoDB using the function from database.py
    try:
        if st.session_state.url:
            st.success("Scraped content saved to DynamoDB successfully!")

    except Exception as e:
        st.error(f"Failed to store content in DynamoDB: {e}")

# Check if DOM content exists and is valid
if "dom_content" in st.session_state and st.session_state.dom_content:
    # Ask the user to describe what they want to parse (optional)
    parse_description = st.text_area("Describe what you want to parse:")

    # Show the "Parse Content" button
    if st.button("Parse Content"):
        if not parse_description:
            st.warning("Please enter a description of what you want to parse.")  # Warning if description is empty
        else:
            st.write("Parsing the content...")

            # Split the content into chunks for parsing
            dom_chunks = split_dom_content(st.session_state.dom_content)
            result = parse_with_gemini(dom_chunks, parse_description)
            st.write(result)

else:
    # Error message if DOM content is not available when clicking "Parse Content"
    st.error("Please scrape a website first.")
