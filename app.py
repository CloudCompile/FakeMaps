import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import osmnx as ox
import networkx as nx
import time
import streamlit.components.v1 as components

# Streamlit settings
st.set_page_config(layout="wide")
st.title("🗺️ Totally Not Google Maps™")

geolocator = Nominatim(user_agent="fakemaps")

# 1. Get user location via JS
st.markdown("## 📍 Live Location Access")

# Run JavaScript in the browser to get location
location_code = """
<script>
navigator.geolocation.getCurrentPosition(
    (position) => {
        const coords = position.coords.latitude + "," + position.coords.longitude;
        const input = window.parent.document.querySelector('input[data-testid="stTextInput"]');
        if (input) {
            input.value = coords;
            const event = new Event('input', { bubbles: true });
            input.dispatchEvent(event);
        }
    },
    (error) => {
        alert("Location access denied. Please allow it to use this feature.");
    }
);
</script>
"""

# Render the JS and a hidden input for location
st.write("Getting your live location (you may need to approve it in your browser)...")
components.html(location_code, height=0)

# Input to receive location from JS
live_coords = st.text_input("Your Coordinates (auto-filled)", "")

# Try parsing the coordinates
user_coords = None
if "," in live_coords:
    try:
        lat, lon = map(float, live_coords.split(","))
        user_coords = (lat, lon)
        st.success(f"📍 Location detected: {user_coords}")
    except ValueError:
        st.error("Could not parse the location coordinates.")

# If no valid user location found, stop
if user_coords is None:
    st.warning("Waiting for your live location...")
    st.stop()

# 2. Destination search
st.sidebar.header("Search Destination")
dest_address = st.sidebar.text_input("Where to?", "Central Park, New York")

# If both are provided and user clicked "Get Directions"
if st.sidebar.button("Get Directions"):
    dest_location = geolocator.geocode(dest_address)
    if not dest_location:
        st.error("Destination not found.")
        st.stop()

    dest_coords = (dest_location.latitude, dest_location.longitude)

    # 3. Load the street network for walking
    G = ox.graph_from_point(user_coords, dist=3000, network_type="walk")

    orig_node = ox.nearest_nodes(G, user_coords[1], user_coords[0])
    dest_node = ox.nearest_nodes(G, dest_coords[1], dest_coords[0])

    route = nx.shortest_path(G, orig_node, dest_node, weight="length")
    route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route]

    # 4. Map UI with user location and destination
    m = folium.Map(location=user_coords, zoom_start=14)
    folium.Marker(user_coords, tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(dest_coords, tooltip="Destination", icon=folium.Icon(color="red")).add_to(m)
    folium.PolyLine(route_coords, color="blue", weight=5).add_to(m)

    st.subheader("🧭 Step-by-Step Navigation")
    with st.expander("Open Map"):
        st_folium(m, width=700, height=500)

    # 5. Step-by-step UI for live navigation
    step_count = len(route_coords)
    step = st.number_input("Step", min_value=1, max_value=step_count, value=1, step=1)

    # Show the current step marker
    live_map = folium.Map(location=route_coords[step - 1], zoom_start=16)
    folium.Marker(route_coords[step - 1], tooltip=f"Step {step}", icon=folium.Icon(color="blue")).add_to(live_map)
    folium.PolyLine(route_coords, color="blue", weight=4).add_to(live_map)

    st.write(f"You're on step {step} of {step_count}")
    st_folium(live_map, width=700, height=500)

    # Optional auto-stepper to simulate live navigation
    if st.button("▶️ Start Navigation"):
        for i in range(step, step_count + 1):
            live_map = folium.Map(location=route_coords[i - 1], zoom_start=16)
            folium.Marker(route_coords[i - 1], tooltip=f"Step {i}", icon=folium.Icon(color="blue")).add_to(live_map)
            folium.PolyLine(route_coords, color="blue", weight=4).add_to(live_map)

            st.write(f"Step {i} of {step_count}")
            st_folium(live_map, width=700, height=500)
            time.sleep(1)
            st.experimental_rerun()  # Restarts the script for next step
