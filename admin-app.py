import streamlit as st
from github import Github

st.set_page_config(page_title="Family Calendar Admin", page_icon="📅", layout="wide")
st.title("📅 Calendar Sync Admin")

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

if 'cal_list' not in st.session_state:
    contents = repo.get_contents("calendars.txt")
    st.session_state.file_sha = contents.sha
    current_text = contents.decoded_content.decode()
    lines = current_text.strip().split('\n')
    st.session_state.cal_list = []
    for line in lines:
        if ':' in line:
            # Format is Name|Emoji:URL
            parts = line.split(':', 1)
            meta, url = parts[0], parts[1]
            if '|' in meta:
                name, emoji = meta.split('|', 1)
            else:
                name, emoji = meta, "📅"
            st.session_state.cal_list.append({"name": name.strip(), "emoji": emoji.strip(), "url": url.strip()})

any_errors = False

st.subheader("Current Calendars")
for i, cal in enumerate(st.session_state.cal_list):
    col1, col2, col3, col4 = st.columns([1, 0.5, 3, 0.5])
    with col1:
        name_val = st.text_input(f"Name {i}", value=cal['name'], key=f"n_{i}", label_visibility="collapsed")
        if ":" in name_val or "|" in name_val:
            st.error("No : or | allowed")
            any_errors = True
    with col2:
        emoji_val = st.text_input(f"Emoji {i}", value=cal['emoji'], key=f"e_{i}", label_visibility="collapsed")
    with col3:
        url_val = st.text_input(f"URL {i}", value=cal['url'], key=f"u_{i}", label_visibility="collapsed")
    with col4:
        if st.button("🗑️", key=f"d_{i}"):
            st.session_state.cal_list.pop(i)
            st.rerun()
    st.session_state.cal_list[i] = {"name": name_val, "emoji": emoji_val, "url": url_val}

st.divider()
st.subheader("Add New")
n_col1, n_col2, n_col3, n_col4 = st.columns([1, 0.5, 3, 1])
with n_col1: new_name = st.text_input("New Name", key="new_n")
with n_col2: new_emoji = st.text_input("Emoji", value="📅", key="new_e")
with n_col3: new_url = st.text_input("New URL", key="new_u")
with n_col4:
    if st.button("➕ Add") and new_name and new_url:
        st.session_state.cal_list.append({"name": new_name, "emoji": new_emoji, "url": new_url})
        st.rerun()

if st.button("💾 Save All Changes", type="primary", disabled=any_errors):
    # Format: Name|Emoji:URL
    final_text = "\n".join([f"{c['name']}|{c['emoji']}:{c['url']}" for c in st.session_state.cal_list])
    repo.update_file("calendars.txt", "Update emojis", final_text, st.session_state.file_sha)
    st.success("Saved!")
    del st.session_state.cal_list
    st.rerun()
    
