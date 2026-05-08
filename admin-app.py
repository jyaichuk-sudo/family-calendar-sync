import streamlit as st
from github import Github
import os

# --- APP SETUP ---
st.set_page_config(page_title="Family Calendar Admin", page_icon="📅")
st.title("📅 Calendar Sync Admin")

# Pulling credentials from Streamlit's hidden vault
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"] # e.g. "yourname/family-calendar-sync"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# --- LOAD CURRENT LIST ---
contents = repo.get_contents("calendars.txt")
current_text = contents.decoded_content.decode()

st.subheader("Current Calendars")
updated_text = st.text_area("Edit your links (Format: Name:URL)", value=current_text, height=300)

if st.button("Save & Sync Now"):
    try:
        # Update the file on GitHub
        repo.update_file(
            contents.path, 
            "Admin Update: Updated calendar links via Web UI", 
            updated_text, 
            contents.sha
        )
        st.success("✅ Changes saved! The 'Robot' will sync in the next hour, or you can trigger it in Actions.")
    except Exception as e:
        st.error(f"❌ Error: {e}")

st.info("💡 Changes made here update the 'calendars.txt' file in your GitHub repository automatically.")
