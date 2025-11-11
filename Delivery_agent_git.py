# ai_logistics_agent.py
# ---------------------------------------
# AI Logistics Planner with Streamlit + Gemini GenAI + File Persistence
# Roles:
#   - Company Representative
#   - Delivery Boy
# Features:
#   - GenAI-based priority reasoning
#   - Manual route reoptimization
#   - Shared state via local JSON file
#   - Auto assignment for delivery boys
#   - Google Maps–style visualization
# ---------------------------------------

import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import random
import os
from math import radians, sin, cos, sqrt, atan2
import folium
from streamlit_folium import st_folium

# ---------------------------------------
# 🔹 Gemini API Setup (Hardcoded)
# ---------------------------------------
API_KEY = "*********"
genai.configure(api_key=API_KEY)

DATA_FILE = "deliveries.json"

# ---------------------------------------
# 🔹 Utilities
# ---------------------------------------
def random_coord(base_lat=22.57, base_lon=88.36):
    return base_lat + random.uniform(-0.05, 0.05), base_lon + random.uniform(-0.05, 0.05)

def sanitize_deliveries(deliveries):
    safe = []
    for i, d in enumerate(deliveries):
        d = d.copy()
        d.setdefault("delivery_id", f"D{i+1}")
        d.setdefault("item", f"Package {i+1}")
        d.setdefault("location", f"Location {i+1}")
        if "lat" not in d or "lon" not in d:
            d["lat"], d["lon"] = random_coord()
        d.setdefault("assigned_agent", random.choice(["Ravi", "Amit", "Suman", "Priya", "Rohit"]))
        d.setdefault("priority_label", random.choice(["High", "Medium", "Low"]))
        d.setdefault("urgency_score", random.randint(3, 9))
        d.setdefault("reason", "Default fallback priority.")
        safe.append(d)
    return safe

def save_deliveries(deliveries):
    with open(DATA_FILE, "w") as f:
        json.dump(deliveries, f, indent=2)

def load_deliveries():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

# ---------------------------------------
# 🧠 GenAI Agent
# ---------------------------------------
class GenAIAgent:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def analyze_priorities(self, deliveries):
        prompt = f"""
        You are an intelligent logistics planner.
        Analyze each delivery and assign priorities (High, Medium, Low)
        semantically based on the nature of the item (not rules).

        Input Deliveries:
        {json.dumps(deliveries, indent=2)}

        Return JSON like:
        [
          {{
            "delivery_id": "<id>",
            "item": "<item>",
            "location": "<location>",
            "priority_label": "<High|Medium|Low>",
            "urgency_score": <1-10>,
            "reason": "<why>",
            "lat": <float>,
            "lon": <float>,
            "assigned_agent": "<agent>"
          }}
        ]
        """
        try:
            response = self.model.generate_content(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)
            return data, "✅ GenAI analyzed priorities successfully."
        except Exception as e:
            return sanitize_deliveries(deliveries), f"⚠️ Fallback: {e}"

    def optimize_routes(self, deliveries, manual_event=None):
        context = f"Manual event: {manual_event}" if manual_event else "No manual event."
        prompt = f"""
        You are a route optimization AI.
        Reassign or reroute deliveries if needed based on this event:
        "{manual_event if manual_event else 'None'}"

        Example: If rally or flood affects an area, reassign deliveries to other agents or alter routes.

        Input Deliveries:
        {json.dumps(deliveries, indent=2)}

        Return valid JSON with possibly updated 'assigned_agent' and 'reason'.
        """
        try:
            response = self.model.generate_content(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            optimized = json.loads(text)
            base_map = {d["delivery_id"]: d for d in deliveries}
            merged = [{**base_map.get(o["delivery_id"], {}), **o} for o in optimized]
            return merged, "✅ GenAI re-optimized routes successfully."
        except Exception as e:
            return sanitize_deliveries(deliveries), f"⚠️ Optimization fallback: {e}"

# ---------------------------------------
# 🗺️ Map
# ---------------------------------------
def render_map(deliveries, draw_routes=True):
    m = folium.Map(location=[22.57, 88.36], zoom_start=12)
    agent_colors = {
        "Ravi": "red",
        "Amit": "blue",
        "Suman": "green",
        "Priya": "purple",
        "Rohit": "orange",
    }

    for agent in set(d["assigned_agent"] for d in deliveries):
        agent_deliveries = [d for d in deliveries if d["assigned_agent"] == agent]
        color = agent_colors.get(agent, "gray")
        coords = []

        for d in agent_deliveries:
            coords.append((d["lat"], d["lon"]))
            popup = f"""
            <b>{d['item']}</b><br>
            {d['location']}<br>
            Priority: {d['priority_label']}<br>
            Agent: {agent}<br>
            Reason: {d['reason']}
            """
            folium.Marker(
                [d["lat"], d["lon"]],
                popup=popup,
                tooltip=f"{d['delivery_id']}: {d['item']}",
                icon=folium.Icon(color=color),
            ).add_to(m)

        if draw_routes and len(coords) > 1:
            folium.PolyLine(coords, color=color, weight=3, opacity=0.6).add_to(m)

    st_folium(m, width=800, height=500)

# ---------------------------------------
# 🔐 Login
# ---------------------------------------
CREDENTIALS = {
    "rep": {"password": "rep123", "role": "company"},
    "ravi": {"password": "ravi123", "role": "agent"},
    "amit": {"password": "amit123", "role": "agent"},
    "suman": {"password": "suman123", "role": "agent"},
    "priya": {"password": "priya123", "role": "agent"},
    "rohit": {"password": "rohit123", "role": "agent"},
}

def login_screen():
    st.title("🔐 AI Logistics Login")
    username = st.text_input("Username").strip().lower()
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in CREDENTIALS and CREDENTIALS[username]["password"] == password:
            st.session_state["user_role"] = (
                "Company Representative" if CREDENTIALS[username]["role"] == "company" else "Delivery Boy"
            )
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("Invalid credentials. Try rep/rep123 or ravi/ravi123 etc.")

# ---------------------------------------
# 🧩 Main App
# ---------------------------------------
def main():
    st.set_page_config(page_title="AI Logistics Planner", layout="wide")
    if "user_role" not in st.session_state:
        login_screen()
        return

    role = st.session_state["user_role"]
    username = st.session_state["username"]
    genai_agent = GenAIAgent()

    st.sidebar.title("🔄 Actions")
    if st.sidebar.button("Logout"):
        for key in ["user_role", "username"]:
            st.session_state.pop(key, None)
        st.rerun()

    # -------------------------------
    # Company Representative
    # -------------------------------
    if role == "Company Representative":
        st.title("🏢 Company Logistics Dashboard")

        if st.button("🚚 Generate Deliveries"):
            items = [
                "Insulin Vial for Apollo Pharmacy",
                "Laptop for TechPark Office",
                "Groceries for South City Mall",
                "Poster Banners for College Fest",
                "Blood Pressure Monitor for Clinic",
            ]
            deliveries = []
            for i, item in enumerate(items):
                lat, lon = random_coord()
                deliveries.append({
                    "delivery_id": f"D{i+1}",
                    "item": item,
                    "location": random.choice(["Salt Lake", "New Town", "Park Street", "Howrah", "Dumdum"]),
                    "lat": lat,
                    "lon": lon,
                    "assigned_agent": random.choice(["Ravi", "Amit", "Suman", "Priya", "Rohit"])
                })
            deliveries = sanitize_deliveries(deliveries)
            save_deliveries(deliveries)
            st.success("✅ Deliveries generated and saved successfully.")

        deliveries = load_deliveries()
        if deliveries:
            st.subheader("📋 Current Deliveries")
            st.dataframe(pd.DataFrame(deliveries))

            if st.button("🧠 Analyze Priorities with GenAI"):
                prioritized, msg = genai_agent.analyze_priorities(deliveries)
                save_deliveries(sanitize_deliveries(prioritized))
                st.success(msg)

            manual_event = st.text_input("⚙️ Manual Event (e.g., 'Rally in Park Street')")
            if st.button("🔁 Optimize Routes (GenAI)"):
                optimized, msg = genai_agent.optimize_routes(deliveries, manual_event)
                save_deliveries(sanitize_deliveries(optimized))
                st.success(msg)

            st.subheader("🗺️ Optimized Delivery Map")
            render_map(load_deliveries())

    # -------------------------------
    # Delivery Boy
    # -------------------------------
    else:
        st.title(f"🚴 Delivery Dashboard - {username.capitalize()}")
        deliveries = load_deliveries()
        assigned = [
            d for d in deliveries if d.get("assigned_agent", "").lower() == username.lower()
        ]

        if not assigned:
            st.warning("No deliveries currently assigned to you.")
            # Auto assign one randomly for demonstration
            if deliveries:
                random_delivery = random.choice(deliveries)
                random_delivery["assigned_agent"] = username.capitalize()
                save_deliveries(deliveries)
                st.info(f"✅ Auto-assigned {random_delivery['delivery_id']} to you.")
                assigned = [random_delivery]

        st.subheader("📋 Your Deliveries")
        st.dataframe(pd.DataFrame(assigned))
        st.subheader("🗺️ Your Route Map")
        render_map(assigned)

# ---------------------------------------
if __name__ == "__main__":
    main()
