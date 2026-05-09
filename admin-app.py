import streamlit as st
from github import Github

# --- APP SETUP ---
st.set_page_config(page_title="Family Calendar Admin", page_icon="📅", layout="wide")
st.title("📅 Calendar Sync Admin")

# Pulling credentials
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# --- LOAD DATA (Run only once per session or on save) ---
if 'cal_list' not in st.session_state:
    contents = repo.get_contents("calendars.txt")
    st.session_state.file_sha = contents.sha
    current_text = contents.decoded_content.decode()
    lines = current_text.strip().split('\n')
    st.session_state.cal_list = []
    for line in lines:
        if ':' in line:
            name, url = line.split(':', 1)
            st.session_state.cal_list.append({"name": name.strip(), "url": url.strip()})

# --- UI: MANAGE EXISTING ---
st.subheader("Current Calendars")
to_delete = []

for i, cal in enumerate(st.session_state.cal_list):
    col1, col2, col3 = st.columns([1, 3, 0.5])
    with col1:
        st.session_state.cal_list[i]['name'] = st.text_input(f"Name {i}", value=cal['name'], key=f"name_{i}", label_visibility="collapsed")
    with col2:
        st.session_state.cal_list[i]['url'] = st.text_input(f"URL {i}", value=cal['url'], key=f"url_{i}", label_visibility="collapsed")
    with col3:
        if st.button("🗑️", key=f"btn_del_{i}"):
            st.session_state.cal_list.pop(i)
            st.rerun()

st.divider()

# --- UI: ADD NEW ---
st.subheader("Add New Calendar")
new_col1, new_col2, new_col3 = st.columns([1, 3, 1])
with new_col1:
    new_name = st.text_input("New Name", key="new_name_input")
with new_col2:
    new_url = st.text_input("New URL", key="new_url_input")
with new_col3:
    if st.button("➕ Add Entry"):
        if new_name and new_url:
            st.session_state.cal_list.append({"name": new_name, "url": new_url})
            st.success(f"Added {new_name}!")
            st.rerun() # This refreshes the list above immediately
        else:
            st.warning("Enter both a name and a URL.")

st.divider()

# --- SAVE TO GITHUB ---
if st.button("💾 Save All Changes to GitHub", type="primary"):
    # Format the data back to text
    final_text = "\n".join([f"{c['name']}:{c['url']}" for c in st.session_state.cal_list])
    
    try:
        repo.update_file(
            "calendars.txt", 
            "Admin UI Update via Session State", 
            final_text, 
            st.session_state.file_sha
        )
        st.success("✅ Changes pushed to GitHub! Syncing now...")
        # Clear state to force a fresh pull from GitHub next time
        del st.session_state.cal_list
        st.rerun()
    except Exception as e:
        st.error(f"❌ GitHub Error: {e}")
        
