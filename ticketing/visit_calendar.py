"""Pop-up visit calendar and Singapore public-holiday classification."""
import calendar  
from datetime import date, datetime, timedelta, timezone   
import streamlit as st

# Include substitute Mondays when a public holiday falls on Sunday.
PUBLIC_HOLIDAYS = {
    2026: {
        "2026-01-01", "2026-02-17", "2026-02-18", "2026-03-21",
        "2026-04-03", "2026-05-01", "2026-05-27", "2026-05-31",
        "2026-06-01", "2026-08-09", "2026-08-10", "2026-11-08",
        "2026-11-09", "2026-12-25",
    },
    2027: {
        "2027-01-01", "2027-02-06", "2027-02-07", "2027-02-08",
        "2027-03-10", "2027-03-26", "2027-05-01", "2027-05-17",
        "2027-05-20", "2027-08-09", "2027-10-28", "2027-12-25",
    },
}


def visit_period(visit_date):
    """Use a single classification rule for the calendar and ticket pricing."""
    if visit_date.year not in PUBLIC_HOLIDAYS:
        raise ValueError("Public holiday dates have not been configured for this year.")
    is_holiday = visit_date.isoformat() in PUBLIC_HOLIDAYS[visit_date.year]
    return "Peak" if visit_date.weekday() >= 4 or is_holiday else "Off-Peak"


def _select_day(selected_date):
    """Update the selected date before Streamlit rerenders the booking summary."""
    st.session_state.visit_date = selected_date


def visit_calendar():
    """Return the selected date from a coloured, keyboard-accessible pop-up calendar."""
    today = datetime.now(timezone(timedelta(hours=8))).date()
    # Limit available years to those with verified holiday data.
    initial_date = today if today.year in PUBLIC_HOLIDAYS else date(min(PUBLIC_HOLIDAYS), 1, 1)

    if "visit_date" not in st.session_state:
        st.session_state.visit_date = initial_date
    selected = st.session_state.visit_date

    # Scope colour styles
    st.markdown('''<style>
    [class*="st-key-visit_day_"] button {
        border-radius: 50%; width: 2.3rem; min-width: 2.3rem;
        height: 2.3rem; min-height: 2.3rem; padding: 0; margin: auto;
    }
    [class*="st-key-visit_day_peak_"] button {
        background: #ffedd5; color: #7c2d12; border: 1px solid #fb923c;
    }
    [class*="st-key-visit_day_offpeak_"] button {
        background: #ccfbf1; color: #134e4a; border: 1px solid #2dd4bf;
    }
    [class*="st-key-visit_day_"] button:hover { filter: brightness(.94); }
    [class*="st-key-visit_day_"] button:focus-visible {
        outline: 3px solid #2563eb; outline-offset: 2px;
    }
    [class*="st-key-visit_day_"][class*="_selected"] button {
        outline: 3px solid #2563eb; outline-offset: 2px;
    }
    .visit-legend { display: flex; flex-wrap: wrap; gap: 12px; font-size: 14px; margin: 12px 0; }
    .visit-legend span { display: inline-flex; align-items: center; gap: 6px; }
    .visit-dot { width: 14px; height: 14px; border-radius: 50%; display: inline-block; }
    </style>''', unsafe_allow_html=True)

    st.write("Visit date")
    with st.popover(selected.strftime("%A, %d %B %Y"), use_container_width=True):
        st.markdown("**Choose your visit date**")
        year_column, month_column = st.columns([1, 2])
        year = year_column.selectbox("Year", sorted(PUBLIC_HOLIDAYS),
                                     index=sorted(PUBLIC_HOLIDAYS).index(selected.year), key="visit_calendar_year")
        month = month_column.selectbox("Month", list(range(1, 13)), index=selected.month - 1,
                                      format_func=lambda value: calendar.month_name[value], key="visit_calendar_month")
        st.markdown('''<div class="visit-legend">
        <span><i class="visit-dot" style="background:#ccfbf1;border:1px solid #2dd4bf"></i>Off-peak</span>
        <span><i class="visit-dot" style="background:#ffedd5;border:1px solid #fb923c"></i>Peak</span>
        <span><i class="visit-dot" style="border:3px solid #2563eb"></i>Selected</span>
        </div>''', unsafe_allow_html=True)

        for column, weekday in zip(st.columns(7), calendar.day_abbr):
            column.markdown(f"**{weekday}**")
            
        for week in calendar.monthcalendar(year, month):
            for column, day_number in zip(st.columns(7), week):
                if day_number == 0:
                    column.write("")  # Keep empty cells aligned before and after the month.
                    continue
                day = date(year, month, day_number)
                period = visit_period(day)
                colour_key = "peak" if period == "Peak" else "offpeak"
                selection_key = "_selected" if day == selected else ""
                holiday_label = " · Public Holiday" if day.isoformat() in PUBLIC_HOLIDAYS[year] else ""
                column.button(
                    str(day_number), key=f"visit_day_{colour_key}_{day.isoformat()}{selection_key}",
                    help=f"{day.strftime('%A, %d %B %Y')} · {period}{holiday_label}",
                    on_click=_select_day, args=(day,),
                )
        st.caption("Off-peak · Monday–Thursday. Peak · Friday–Sunday and Singapore Public Holidays.")
        st.caption("Holiday calendar available for 2026–2027.")
    return selected
