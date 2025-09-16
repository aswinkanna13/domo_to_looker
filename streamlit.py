import streamlit as st
import requests
import pandas as pd
import os

st.title("📊 Domo Dashboards, Cards & Datasets Viewer")

# Session state initialization
if 'instance' not in st.session_state:
    st.session_state.instance = ""
if 'developer_token' not in st.session_state:
    st.session_state.developer_token = ""
if 'pages' not in st.session_state:
    st.session_state.pages = []
if 'selected_page_id' not in st.session_state:
    st.session_state.selected_page_id = None
if 'datasets' not in st.session_state:
    st.session_state.datasets = []

# Inputs
st.session_state.instance = st.text_input(
    "Enter your Domo Instance (e.g., squareshift-co-34):",
    st.session_state.instance
)
st.session_state.developer_token = st.text_input(
    "Enter your Domo Developer Token:",
    st.session_state.developer_token,
    type="password"
)

def get_headers():
    return {
        "X-DOMO-Developer-Token": st.session_state.developer_token,
        "Content-Type": "application/json"
    }

# ------------------- DATASETS FETCH -------------------
def fetch_datasets():
    """Fetch all datasets for the given instance"""
    url = f"https://{st.session_state.instance}.domo.com/api/data/v3/datasources"
    resp = requests.get(url, headers=get_headers())

    if resp.status_code != 200:
        st.error(f"❌ Failed to fetch datasets: {resp.status_code} {resp.text}")
        return []

    data = resp.json()

    # Your response has "dataSources" key
    if isinstance(data, dict) and "dataSources" in data:
        return data["dataSources"]

    # Fallback
    st.warning("⚠️ Unexpected dataset response format")
    st.json(data)
    return []

# Button to fetch datasets
if st.button("Fetch Datasets"):
    if not st.session_state.instance or not st.session_state.developer_token:
        st.warning("⚠️ Please provide both instance and developer token.")
    else:
        st.session_state.datasets = fetch_datasets()
        if st.session_state.datasets:
            st.success(f"✅ Retrieved {len(st.session_state.datasets)} datasets")

# Display datasets if fetched
if st.session_state.datasets:
    df_datasets = pd.DataFrame([
        {
            "Dataset ID": ds.get("id", "N/A"),
            "Name": ds.get("name", "N/A"),
            "Type": ds.get("type", "N/A")
        }
        for ds in st.session_state.datasets if isinstance(ds, dict)
    ])
    st.subheader("📂 Available Datasets")
    st.dataframe(df_datasets, use_container_width=True)


# ------------------- DASHBOARDS FETCH -------------------
def fetch_pages():
    """Fetch all dashboards (pages)"""
    url = f"https://{st.session_state.instance}.domo.com/api/content/v1/pages"
    resp = requests.get(url, headers=get_headers())
    if resp.status_code == 200:
        return resp.json()
    else:
        st.error(f"❌ Failed to fetch dashboards: {resp.status_code} {resp.text}")
        return []

def fetch_cards(page_id):
    """Fetch all cards inside a page"""
    url = f"https://{st.session_state.instance}.domo.com/api/content/v1/pages/{page_id}/cards"
    resp = requests.get(url, headers=get_headers())
    if resp.status_code == 200:
        return resp.json()
    else:
        st.error(f"❌ Failed to fetch cards: {resp.status_code} {resp.text}")
        return []

# Button to fetch dashboards
if st.button("Fetch Dashboards"):
    if not st.session_state.instance or not st.session_state.developer_token:
        st.warning("⚠️ Please provide both instance and developer token.")
    else:
        st.session_state.pages = fetch_pages()
        if st.session_state.pages:
            st.success(f"✅ Retrieved {len(st.session_state.pages)} dashboards")

# Display dashboards if fetched
if st.session_state.pages:
    df_pages = pd.DataFrame([
        {
            "Page ID": p.get("id"),
            "Title": p.get("title"),
            "Owner": (p.get("owners", [{}])[0].get("displayName")
                      if p.get("owners") else "N/A")
        }
        for p in st.session_state.pages if isinstance(p, dict)
    ])
    st.subheader("📊 Available Dashboards")
    st.dataframe(df_pages, use_container_width=True)

    # Dropdown to select dashboard
    page_map = {p["title"]: p["id"] for p in st.session_state.pages if isinstance(p, dict)}
    selected_title = st.selectbox("Select Dashboard:", list(page_map.keys()))
    st.session_state.selected_page_id = page_map[selected_title]

    # Fetch and display cards for selected dashboard
    if st.session_state.selected_page_id:
        cards = fetch_cards(st.session_state.selected_page_id)
        if cards and isinstance(cards, list):
            df_cards = pd.DataFrame([
                {"Card ID": c.get("id"), "Title": c.get("title")}
                for c in cards if isinstance(c, dict)
            ])
            st.subheader(f"🗂️ Cards in Dashboard: {selected_title} (ID: {st.session_state.selected_page_id})")
            st.dataframe(df_cards, use_container_width=True)
