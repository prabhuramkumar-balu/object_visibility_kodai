import streamlit as st
from datetime import datetime, date
from calendar import monthcalendar, setfirstweekday, MONDAY
from astral.sun import sun
from astral.location import LocationInfo
import pytz
import ephem  # pip install ephem

setfirstweekday(MONDAY)
IST = pytz.timezone("Asia/Kolkata")

# Location for Kodaikanal
latitude = 10 + 13/60 + 50/3600
longitude = 77 + 28/60 + 7/3600
timezone = "Asia/Kolkata"

astral_city = LocationInfo("Kodaikanal", "India", timezone, latitude, longitude)

st.set_page_config(page_title="Kodaikanal Astronomy Calendar", layout="wide")
st.title("📅 Kodaikanal Astronomy Calendar")
st.caption("Sunrise, Sunset, Moon Phase, Moonrise/Set, and Planetary Rise/Set Times (IST, 12-hour format)")

year = st.number_input("Select Year", min_value=1900, max_value=2100, value=date.today().year)
months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
month_name = st.selectbox("Select Month", months)
month_index = months.index(month_name) + 1
calendar = monthcalendar(year, month_index)

days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
cols = st.columns(7)
for i, d in enumerate(days):
    cols[i].markdown(f"**{d}**")

def to_ist_12h(dt_utc):
    if dt_utc == "N/A" or dt_utc is None:
        return "N/A"
    dt_utc = pytz.utc.localize(dt_utc)
    dt_ist = dt_utc.astimezone(IST)
    return dt_ist.strftime("%I:%M %p")

def get_rise_set(observer, body):
    try:
        rise = observer.next_rising(body)
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        rise = None
    try:
        set_ = observer.next_setting(body)
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        set_ = None
    return rise.datetime() if rise else "N/A", set_.datetime() if set_ else "N/A"

for week in calendar:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write(" ")
        else:
            label = f"{day}"
            if date.today() == date(year, month_index, day):
                label = f"🟢 {day}"

            if cols[i].button(label, key=f"{year}-{month_index}-{day}"):
                try:
                    # Date for calculations at noon local time to avoid timezone issues
                    dt_local = datetime(year, month_index, day, 12, 0, 0)
                    dt_utc = pytz.timezone(timezone).localize(dt_local).astimezone(pytz.utc)

                    # Astral sunrise/sunset in IST
                    sun_times = sun(astral_city.observer, date=dt_local, tzinfo=pytz.timezone(timezone))
                    sunrise_ist = sun_times['sunrise'].strftime('%I:%M %p')
                    sunset_ist = sun_times['sunset'].strftime('%I:%M %p')

                    # PyEphem observer
                    observer = ephem.Observer()
                    observer.lat = str(latitude)
                    observer.lon = str(longitude)
                    observer.elevation = 0
                    observer.date = dt_utc

                    # Moon info
                    moon = ephem.Moon(observer)
                    moon_phase = moon.phase  # illumination %

                    moonrise_utc, moonset_utc = get_rise_set(observer, moon)
                    moonrise_ist = to_ist_12h(moonrise_utc)
                    moonset_ist = to_ist_12h(moonset_utc)

                    # Planets dictionary
                    planets = {
                        "Mercury": ephem.Mercury(),
                        "Venus": ephem.Venus(),
                        "Mars": ephem.Mars(),
                        "Jupiter": ephem.Jupiter(),
                        "Saturn": ephem.Saturn(),
                    }

                    planet_times = {}
                    for pname, pbody in planets.items():
                        rise_dt, set_dt = get_rise_set(observer, pbody)
                        planet_times[pname] = (to_ist_12h(rise_dt), to_ist_12h(set_dt))

                    st.markdown("---")
                    st.header(f"Astronomy Data for {dt_local.strftime('%A, %d %B %Y')}")
                    st.subheader("🌅 Sunrise & Sunset")
                    st.write(f"**Sunrise:** {sunrise_ist} IST")
                    st.write(f"**Sunset:** {sunset_ist} IST")

                    st.subheader("🌕 Moon Phase and Moonrise/Moonset")
                    st.write(f"Illumination: **{moon_phase:.1f}%**")
                    st.write(f"**Moonrise:** {moonrise_ist} IST")
                    st.write(f"**Moonset:** {moonset_ist} IST")

                    st.subheader("🪐 Planet Rise/Set Times")
                    for pname, (rise_t, set_t) in planet_times.items():
                        st.write(f"**{pname}** — Rise: {rise_t}, Set: {set_t}")

                except Exception as e:
                    st.error(f"Error retrieving data: {e}")
