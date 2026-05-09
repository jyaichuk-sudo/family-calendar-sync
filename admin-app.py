import streamlit as st
from github import Github

# --- APP SETUP ---
st.set_page_config(page_title="Family Calendar Admin", page_icon="📅", layout="wide")
st.title("📅 Calendar Sync Admin")

# Pulling credentials from Streamlit's secrets
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# --- DATA PROCESSING ---
contents = repo.get_contents("calendars.txt")
current_text = contents.decoded_content.decode()

# Convert the text file into a list of dictionaries
lines = current_text.strip().split('\n')
cal_data = []
for line in lines:
    if ':' in line:
        name, url = line.split(':', 1)
        cal_data.append({"name": name.strip(), "url": url.strip()})

# --- UI FOR EDITING ---
st.subheader("Manage Your Calendar Feeds")
updated_cals = []

# Create rows for each existing calendar
for i, cal in enumerate(cal_data):
    col1, col2, col3 = st.columns([1, 3, 0.5])
    with col1:
        new_name = st.text_input(f"Name {i}", value=cal['name'], label_visibility="collapsed", key=f"name_{i}")
    with col2:
        new_url = st.text_input(f"URL {i}", value=cal['url'], label_visibility="collapsed", key=f"url_{i}")
    with col3:
        delete = st.checkbox("🗑️", key=f"del_{i}")
    
    if not delete:
        updated_cals.append(f"{new_name}:{new_url}")

st.divider()

# --- UI FOR ADDING NEW ---
st.subheader("Add New Calendar")
new_col1, new_col2 = st.columns([1, 3])
with new_col1:
    add_name = st.text_input("Name", placeholder="e.g. Baseball")
with new_col2:
    add_url = st.text_input("URL", placeholder="https://...")

if add_name and add_url:
    if st.button("➕ Add to List"):
        updated_cals.append(f"{add_name}:{add_url}")
        st.info("Added to queue. Press 'Save Changes' below to finalize.")

st.divider()

# --- SAVE LOGIC ---
final_text = "\n".join(updated_cals)

if st.button("💾 Save Changes & Sync", type="primary"):
    try:
        repo.update_file(
            contents.path, 
            "Admin UI Update", 
            final_text, 
            contents.sha
        )
        st.success("✅ Calendars updated successfully! Your family's view will update shortly.")
        # Reload the app to refresh the list
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error saving to GitHub: {e}")
        
