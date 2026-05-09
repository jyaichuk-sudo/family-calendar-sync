import streamlit as st
from github import Github

st.set_page_config(page_title="Family Admin", page_icon="📅", layout="wide")
st.title("📅 Calendar & Countdown Admin")

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# --- CALENDAR SECTION ---
if 'cal_list' not in st.session_state:
    c_file = repo.get_contents("calendars.txt")
    st.session_state.c_sha = c_file.sha
    lines = c_file.decoded_content.decode().strip().split('\n')
    st.session_state.cal_list = []
    for line in lines:
        if ':' in line:
            meta, url = line.split(':', 1)
            name, emoji = meta.split('|', 1) if '|' in meta else (meta, "📅")
            st.session_state.cal_list.append({"name": name, "emoji": emoji, "url": url})

# --- COUNTDOWN SECTION ---
if 'cd_list' not in st.session_state:
    try:
        cd_file = repo.get_contents("countdowns.txt")
        st.session_state.cd_sha = cd_file.sha
        lines = cd_file.decoded_content.decode().strip().split('\n')
        st.session_state.cd_list = [l.split('|') for l in lines if '|' in l]
    except:
        st.session_state.cd_list = []
        st.session_state.cd_sha = None

# UI for Calendars (keeping your existing logic)
st.subheader("Manage Calendars")
for i, cal in enumerate(st.session_state.cal_list):
    col1, col2, col3, col4 = st.columns([1, 0.5, 3, 0.5])
    st.session_state.cal_list[i]['name'] = col1.text_input(f"Name {i}", cal['name'], key=f"n{i}", label_visibility="collapsed")
    st.session_state.cal_list[i]['emoji'] = col2.text_input(f"Emoji {i}", cal['emoji'], key=f"e{i}", label_visibility="collapsed")
    st.session_state.cal_list[i]['url'] = col3.text_input(f"URL {i}", cal['url'], key=f"u{i}", label_visibility="collapsed")
    if col4.button("🗑️", key=f"d{i}"):
        st.session_state.cal_list.pop(i)
        st.rerun()

if st.button("➕ Add Calendar"):
    st.session_state.cal_list.append({"name": "New", "emoji": "📅", "url": ""})
    st.rerun()

st.divider()

# UI for Countdowns
st.subheader("Manage Countdowns")
for i, cd in enumerate(st.session_state.cd_list):
    col1, col2, col3 = st.columns([2, 2, 0.5])
    st.session_state.cd_list[i][0] = col1.text_input(f"Event {i}", cd[0], key=f"cn{i}", label_visibility="collapsed")
    st.session_state.cd_list[i][1] = col2.text_input(f"Date (YYYY-MM-DD)", cd[1], key=f"cd{i}", label_visibility="collapsed")
    if col3.button("🗑️", key=f"cdn{i}"):
        st.session_state.cd_list.pop(i)
        st.rerun()

if st.button("➕ Add Countdown"):
    st.session_state.cd_list.append(["New Event", "2026-12-25"])
    st.rerun()

if st.button("💾 Save Everything", type="primary"):
    # Save Calendars
    cal_text = "\n".join([f"{c['name']}|{c['emoji']}:{c['url']}" for c in st.session_state.cal_list])
    repo.update_file("calendars.txt", "Update calendars", cal_text, st.session_state.c_sha)
    
    # Save Countdowns
    cd_text = "\n".join([f"{c[0]}|{c[1]}" for c in st.session_state.cd_list])
    if st.session_state.cd_sha:
        repo.update_file("countdowns.txt", "Update countdowns", cd_text, st.session_state.cd_sha)
    else:
        repo.create_file("countdowns.txt", "Create countdowns", cd_text)
    
    st.success("Changes Saved!")
    st.rerun()
    
