"""Streamlit layout for the ticket information and booking tabs."""
from uuid import uuid4

import streamlit as st

from visit_calendar import default_visit_date, singapore_today, visit_calendar, visit_period


BOOKING_DEFAULTS = {
    "adults": 0,
    "children": 0,
    "family": False,
    "express_adults": 0,
    "express_children": 0,
    "rental": 0,
    "tour": "None",
}
BOOKING_KEYS = (*BOOKING_DEFAULTS, "visit_date", "visit_calendar_year", "visit_calendar_month")


def render_ticketing_page(mylibrary):
    st.set_page_config(page_title="Tales of Lanfang Tickets", layout="wide")
    st.title("Tales of Lanfang Tickets")
    info_tab, booking_tab = st.tabs(["Prices and visit information", "Book tickets"])
    with info_tab:
        render_visit_information(mylibrary)
    with booking_tab:
        if "checkout_booking" in st.session_state:
            render_checkout()
        else:
            render_booking(mylibrary)


def render_visit_information(mylibrary):
    st.subheader("Peak and off-peak pricings")
    off_peak_card, peak_card = st.columns(2)

    for card, period in [(off_peak_card, "Off-Peak"), (peak_card, "Peak")]:
        with card:
            with st.container(border=True):
                st.subheader(period)
                st.write(mylibrary.VISIT_DAYS[period])
                st.caption("Prices per person")
                adult_column, child_column = st.columns(2)
                adult_column.metric("Adult", f"${mylibrary.admission_price('adult', period):.2f}")
                child_column.metric("Child", f"${mylibrary.admission_price('child', period):.2f}")
    st.caption("Adults are aged 13 and above. Children are aged 12 and below. Public Holidays always use peak prices.")

    st.subheader("Ticket Pricing")
    # Reference the pricing library so displayed rates match the booking calculation.
    price_rows = []

    for category, label in [("adult", "Adult"), ("child", "Child")]:
        for express in [False, True]:
            price_rows.append({
                "Visitor": label,
                "Admission": "Express" if express else "Standard",
                "Off-Peak": f"${mylibrary.admission_price(category, 'Off-Peak', express):.2f}",
                "Peak": f"${mylibrary.admission_price(category, 'Peak', express):.2f}",
            })
    st.table(price_rows)
    st.caption("Express costs twice standard admission. Prices shown are before family savings.")

    tour_column, savings_column = st.columns(2)
    with tour_column:
        with st.container(border=True):
            st.subheader("Guides for your visit")
            st.write(f"**Audio guide rental** · ${mylibrary.PRICES['audio_guide']:.2f} each")
            st.table([
                {"Guided tour": duration, "Per tour guide": f"${price:.2f}"}
                for duration, price in mylibrary.PRICES["tour"].items() if duration != "None"
            ])
            st.write(f"**Maximum {mylibrary.MAX_PEOPLE_PER_GUIDE} visitors per tour guide.** Additional guides are added automatically for larger groups.")
            st.caption("16 visitors need 2 guides. Audio guide and tour fees apply on all visit days.")

    with savings_column:
        with st.container(border=True):
            st.subheader("Family savings")
            st.write(f"**Save {mylibrary.PRICES['family_discount']}% with family tickets**")
            st.markdown(
                "- **Group size** · At least 3 people, including at least 1 child.\n"
                f"- **Family rate** · Up to {mylibrary.MAX_ADULTS_PER_CHILD} adults per child. "
                "Additional adults pay standard admission."
            )
            st.markdown(
                "**How discounts are applied**\n\n"
                "Off-peak savings apply first, followed by eligible family savings. "
                "Audio guides and tours are charged separately."
            )


def reset_booking():
    visit_date = default_visit_date()
    # Write widget values so Streamlit sends the reset values to the browser.
    st.session_state.update(
        BOOKING_DEFAULTS,
        visit_date=visit_date,
        visit_calendar_year=visit_date.year,
        visit_calendar_month=visit_date.month,
    )
    for key in ("checkout_booking", "booking_reference"):
        st.session_state.pop(key, None)


def start_checkout(breakdown, ticket_type, guide_count):
    if st.session_state.visit_date < singapore_today():
        return
    st.session_state.checkout_booking = {
        "selections": {key: st.session_state[key] for key in BOOKING_KEYS},
        "breakdown": breakdown,
        "ticket_type": ticket_type,
        "guide_count": guide_count,
    }


def edit_booking():
    booking = st.session_state.pop("checkout_booking")
    st.session_state.update(booking["selections"])


def confirm_booking():
    visit_date = st.session_state.checkout_booking["selections"]["visit_date"]
    if visit_date >= singapore_today():
        st.session_state.booking_reference = uuid4().hex[:12].upper()


def render_checkout():
    booking = st.session_state.checkout_booking
    selections = booking["selections"]
    breakdown = booking["breakdown"]
    reference = st.session_state.get("booking_reference")
    date_has_passed = selections["visit_date"] < singapore_today()

    st.subheader("Booking confirmation" if reference else "Checkout")
    if reference:
        st.success(f"Booking confirmed. Booking reference: {reference}")

    with st.container(border=True):
        st.write(f"**{booking['ticket_type']} admission**")
        st.write(selections["visit_date"].strftime("%A, %d %B %Y"))
        express_adults = selections["express_adults"]
        express_children = selections["express_children"]
        line_items = [
            ("Adult tickets", str(selections["adults"]), "Adult tickets"),
            ("Child tickets", str(selections["children"]), "Child tickets"),
            ("Express upgrades", f"{express_adults} adult, {express_children} child", "Express upgrade"),
            ("Off-peak discount", "", "Off-peak discount"),
            ("Family discount", "", "Family discount"),
            ("Audio guides", str(selections["rental"]), "Audio guides"),
            (f"{selections['tour']} guided tour", f"{booking['guide_count']} guide(s)", "Group tour"),
        ]
        rows = []
        for label, quantity, price_key in line_items:
            amount = breakdown[price_key]
            if amount:
                sign = "-" if amount < 0 else ""
                rows.append({
                    "Item": label,
                    "Quantity": quantity,
                    "Amount (SGD)": f"{sign}${abs(amount):.2f}",
                })
        st.table(rows)
        total_label = "Total payment" if reference else "Total to pay"
        st.metric(total_label, f"S${breakdown['Total to pay']:.2f}")

    if reference:
        st.button("Book more tickets", on_click=reset_booking)
    else:
        back_column, pay_column = st.columns(2)
        back_column.button("Back to booking", on_click=edit_booking)
        pay_column.button(
            "Make payment", type="primary", on_click=confirm_booking,
            disabled=date_has_passed,
        )
        if date_has_passed:
            st.warning("This visit date has passed. Go back and choose today or a future date.")


def render_booking(mylibrary):
    # A wider input column keeps the live summary alongside the ticket choices.
    choices_column, summary_column = st.columns([3, 2], gap="large")
    with choices_column:
        with st.container(border=True):
            with st.container(horizontal=True, horizontal_alignment="distribute"):
                st.subheader("Your visit")
                st.button("Reset", on_click=reset_booking)
            visit_date = visit_calendar()  # The calendar supplies the visit date automatically.
            date_has_passed = visit_date < singapore_today()
            if date_has_passed:
                st.warning("Choose today or a future date to continue.")
            ticket_type = visit_period(visit_date)  # Use the same rule as the coloured day circles.
            st.write(f"**{ticket_type} admission**")
            st.caption(mylibrary.VISIT_DAYS[ticket_type])
            adult_column, child_column = st.columns(2)
            adults = adult_column.number_input("Adults · ages 13+", min_value=0, step=1, key="adults")
            children = child_column.number_input("Children · ages 0–12", min_value=0, step=1, key="children")
            family = st.checkbox("Apply family savings", key="family")
            family_adults, extra_adults = mylibrary.family_group(adults, children)

            if mylibrary.family_eligible(adults, children):
                st.caption(f"Eligible for family savings on {family_adults} adult(s) and {children} child(ren). {extra_adults} additional adult(s) pay standard admission.")
            elif family:
                st.warning("Family tickets need at least 3 people, including at least 1 child.")
            else:
                st.caption("Family savings require 3 or more visitors, including at least 1 child.")

        with st.container(border=True):
            st.subheader("Express admission")
            st.caption("Choose how many tickets to upgrade. These are included in your visitor counts above.")
            # Reduce saved express quantities when the visitor counts decrease.

            for key, maximum in [("express_adults", adults), ("express_children", children)]:
                st.session_state[key] = min(st.session_state.get(key, 0), maximum)
            adult_column, child_column = st.columns(2)
            express_adults = adult_column.number_input("Adult express tickets", min_value=0, max_value=adults, step=1, key="express_adults")
            express_children = child_column.number_input("Child express tickets", min_value=0, max_value=children, step=1, key="express_children")

        with st.container(border=True):
            st.subheader("Guides and extras")
            rental = st.number_input("Audio guides", min_value=0, step=1, key="rental", help=f"${mylibrary.PRICES['audio_guide']:.2f} per audio guide.")
            tour = st.selectbox("Guided tour", options=list(mylibrary.PRICES["tour"]), key="tour")
            people = adults + children
            guide_count = mylibrary.tour_guides_needed(people) if tour != "None" else 0

            if tour != "None":
                st.caption(f"{guide_count} tour guide(s) for {people} visitors · ${mylibrary.PRICES['tour'][tour]:.2f} per guide · maximum {mylibrary.MAX_PEOPLE_PER_GUIDE} visitors per guide.")

    with summary_column:
        with st.container(border=True):
            st.subheader("Your booking")
            st.caption("Updates automatically as you change your selections.")
            st.write(f"**{ticket_type} admission**")
            st.write(visit_date.strftime("%A, %d %B %Y"))  # Confirm the selected booking date.
            st.write(f"{adults} adult(s) · {children} child(ren)")
            st.write(f"Express upgrades · {express_adults} adult(s), {express_children} child(ren)")

            if family and extra_adults:
                st.caption(f"Family rate covers {family_adults} adult(s) and {children} child(ren). {extra_adults} adult(s) pay standard admission.")
            st.write(f"Audio guides · {rental}")

            if tour != "None":
                st.write(f"{tour} tour · {guide_count} guide(s)")
            st.divider()

            if people == 0:
                st.metric("Total to pay", "$0.00")
                st.info("Add your tickets to see a price breakdown.")

            else:
                try:
                    # Calculate on every rerun using the selected ticket quantities.
                    result = mylibrary.calculate_booking(
                        adults=adults, children=children, rental=rental, ticket_type=ticket_type,
                        family=family, tour=tour,
                        express_adults=express_adults, express_children=express_children,
                    )
                except ValueError as error:
                    st.error(str(error))

                else:
                    st.metric("Total to pay", f"${result['Total to pay']:.2f}")
                    # Show the payable components once and dont show unused extras.
                    for item in ["Basic ticket total", "Express upgrade", "Off-peak discount", "Family discount", "Audio guides", "Group tour"]:
                        amount = result[item]
                        if amount != 0:
                            label_column, amount_column = st.columns([3, 1])
                            label_column.write(item)
                            amount_column.write(f"-${abs(amount):.2f}" if amount < 0 else f"${amount:.2f}")
                    with st.expander("Full price breakdown"):
                        st.table([{"Item": item, "Amount": f"${amount:.2f}"} for item, amount in result.items()])
                    st.button(
                        "Continue to checkout", type="primary", on_click=start_checkout,
                        args=(result, ticket_type, guide_count),
                        disabled=date_has_passed,
                    )
