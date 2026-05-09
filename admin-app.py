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

# --- LOAD DATA ---
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

# Tracking if any name is invalid
any_errors = False

# --- UI: MANAGE EXISTING ---
st.subheader("Current Calendars")
for i, cal in enumerate(st.session_state.cal_list):
    col1, col2, col3 = st.columns([1, 3, 0.5])
    with col1:
        name_val = st.text_input(f"Name {i}", value=cal['name'], key=f"name_{i}", label_visibility="collapsed")
        if ":" in name_val:
            st.error("No colons (:) allowed in names")
            any_errors = True
        st.session_state.cal_list[i]['name'] = name_val
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
    new_name = st.text_input("New Name", key="new_name_input", placeholder="e.g. Baseball")
    if ":" in new_name:
        st.error("Remove the colon")
        any_errors = True
with new_col2:
    new_url = st.text_input("New URL", key="new_url_input", placeholder="https://...")
with new_col3:
    # Disable "Add" button if there's a colon in the new name
    add_disabled = True if ":" in new_name or not new_name or not new_url else False
    if st.button("➕ Add Entry", disabled=add_disabled):
        st.session_state.cal_list.append({"name": new_name, "url": new_url})
        st.rerun()

st.divider()

# --- SAVE TO GITHUB ---
# Disable "Save" button if ANY entry has a colon
if st.button("💾 Save All Changes to GitHub", type="primary", disabled=any_errors):
    final_text = "\n".join([f"{c['name']}:{c['url']}" for c in st.session_state.cal_list])
    try:
        repo.update_file(
            "calendars.txt", 
            "Admin UI Update - Added Colon Validation", 
            final_text, 
            st.session_state.file_sha
        )
        st.success("✅ Changes pushed! Syncing now...")
        del st.session_state.cal_list
        st.rerun()
    except Exception as e:
        st.error(f"❌ GitHub Error: {e}")
elif any_errors:
    st.warning("Please remove all colons from names before saving.")
