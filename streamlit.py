import streamlit as st
import requests
import pandas as pd
import os

st.title("📊 Domo Dashboards, Cards, Datasets & Dataflows Viewer")

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
if 'dataflows' not in st.session_state:
    st.session_state.dataflows = []

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
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

# ------------------- DATASETS FETCH -------------------
def fetch_datasets():
    """Fetch all datasets for the given instance"""
    url = f"https://{st.session_state.instance}.domo.com/api/data/v3/datasources/"
    try:
        resp = requests.get(url, headers=get_headers())
        resp.raise_for_status()
        data = resp.json()
        return data.get("dataSources", [])
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Failed to fetch datasets: {e}")
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
            dashboards_data = []
            for p in st.session_state.pages:
                if isinstance(p, dict):
                    page_id = p.get("id")
                    cards = fetch_cards(page_id)
                    card_count = len(cards) if isinstance(cards, list) else 0
                    dashboards_data.append({
                        "Page ID": page_id,
                        "Title": p.get("title"),
                        "Owner": (p.get("owners", [{}])[0].get("displayName")
                                  if p.get("owners") else "N/A"),
                        "Number of Cards": card_count
                    })

            df_pages = pd.DataFrame(dashboards_data)

            num_dashboards = len(df_pages)
            avg_cards = df_pages["Number of Cards"].mean() if num_dashboards > 0 else 0

            st.success(f"✅ Retrieved {num_dashboards} dashboards")

            st.subheader("📊 Available Dashboards with Card Counts")
            st.dataframe(df_pages, use_container_width=True)

            st.write(f"**📌 Average number of cards per dashboard:** {avg_cards:.2f}")

            page_map = {row["Title"]: row["Page ID"] for _, row in df_pages.iterrows()}
            selected_title = st.selectbox("Select Dashboard:", list(page_map.keys()))
            st.session_state.selected_page_id = page_map[selected_title]

            if st.session_state.selected_page_id:
                cards = fetch_cards(st.session_state.selected_page_id)
                if cards and isinstance(cards, list):
                    df_cards = pd.DataFrame([
                        {"Card ID": c.get("id"), "Title": c.get("title")}
                        for c in cards if isinstance(c, dict)
                    ])
                    st.subheader(f"🗂️ Cards in Dashboard: {selected_title} (ID: {st.session_state.selected_page_id})")
                    st.dataframe(df_cards, use_container_width=True)

# ------------------- DATAFLOWS (Magic ETL) -------------------
def fetch_dataflows():
    url = f"https://{st.session_state.instance}.domo.com/api/dataprocessing/v1/dataflows/"
    try:
        resp = requests.get(url, headers=get_headers())
        resp.raise_for_status()
        response = resp.json()
        return response if isinstance(response, list) else []
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Failed to fetch Magic ETL: {e}")
        return []

# Button to fetch dataflows
if st.button("Fetch Dataflows"):
    if not st.session_state.instance or not st.session_state.developer_token:
        st.warning("⚠️ Please provide both instance and developer token.")
    else:
        st.session_state.dataflows = fetch_dataflows()
        if st.session_state.dataflows:
            st.success(f"✅ Retrieved {len(st.session_state.dataflows)} Magic ETLs")

# Display dataflows if fetched
if st.session_state.dataflows:
    df_dataflows = pd.DataFrame([
        {
            "Dataflow ID": df.get("id", "N/A"),
            "Name": df.get("name", "N/A"),
            "no_of_inputs": len(df.get("inputs", [])),
            "no_of_outputs": len(df.get("outputs", [])),
            "inputs": [inp.get("dataSourceId") for inp in df.get("inputs", [])],
            "outputs": [out.get("dataSourceId") for out in df.get("outputs", [])]
        }
        for df in st.session_state.dataflows if isinstance(df, dict)
    ])
    st.subheader("🛠️ Available Magic ETLs")
    st.dataframe(df_dataflows, use_container_width=True)
