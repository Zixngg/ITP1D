"""Pricing catalogue and calculations for Tales of Lanfang bookings."""
from decimal import Decimal, ROUND_HALF_UP  # Use exact decimal arithmetic for money.

# Change prices here so the information page and booking use the same rates.
PRICES = {
    "adult": 10,  # Standard peak admission for ages 13 and above.
    "child": 5,  # Standard peak admission for ages 12 and below.
    "audio_guide": 3,  # Rental charge per audio guide.
    "express_multiplier": 2,  # Express admission costs twice standard admission.
    "tour": {"None": 0, "Half day": 15, "Full day": 25},  # Charge per tour guide.
    "period_discount": {"Peak": 0, "Off-Peak": 10},  # Percentage off admission.
    "family_discount": 15,  # Percentage off eligible family admission.
}
DISCOUNT_CODES = {"WELCOME10": 10, "LANFANG20": 20}  # Code and percentage discount.
CHILD_MAX_AGE = 12  # Inclusive upper age for a child ticket.
MAX_ADULTS_PER_CHILD = 4  # Family tickets allow at most 4 adults for each child.
MAX_PEOPLE_PER_GUIDE = 15  # Each tour guide can accompany at most 15 visitors.
VISIT_DAYS = {
    "Off-Peak": "Monday-Thursday, excluding Public Holidays",
    "Peak": "Friday-Sunday and all Public Holidays",
}


def _quantity(value):
    # Function to check for input to ensure it is a non-negative whole number, rejecting negative quantities, fractions, and Boolean values.
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("Quantities must be non-negative whole numbers.")
    return value


def _money(value):
    # Round to cents using conventional half-up rounding.
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def admission_price(category, ticket_type="Peak", express=False):
    #  Return the displayed per-person rate before family or code discounts.
    price = Decimal(str(PRICES[category]))  # Start from the peak admission price.
    multiplier = PRICES["express_multiplier"] if express else 1
    discount = Decimal(str(PRICES["period_discount"][ticket_type])) / 100
    return _money(price * multiplier * (1 - discount))


def calculate_total(adults, children):
    """Keep the original helper returning basic adult and child subtotals."""
    return (_quantity(adults) * PRICES["adult"],
            _quantity(children) * PRICES["child"])


def audio_guides(items):
    """Calculate the rental cost for the requested number of audio guides."""
    return _quantity(items) * PRICES["audio_guide"]


def family_group(adults, children):
    """Return family-rate adults and leftover adults who pay the standard price."""
    adults = _quantity(adults)
    children = _quantity(children)
    family_adults = min(adults, MAX_ADULTS_PER_CHILD * children) if children else 0
    if children < 1 or family_adults + children < 3:
        return 0, adults
    return family_adults, adults - family_adults


def family_eligible(adults, children):
    """A family unit needs at least three visitors and at least one child."""
    family_adults, _extra_adults = family_group(adults, children)
    return family_adults + _quantity(children) >= 3 and children >= 1


def tour_guides_needed(people):
    """Round up so any remaining visitors receive another tour guide."""
    return (_quantity(people) + MAX_PEOPLE_PER_GUIDE - 1) // MAX_PEOPLE_PER_GUIDE


def calculate_booking(adults, children, rental=0, ticket_type="Peak",
                      express=False, family=False, tour="None", discount_code="",
                      express_adults=0, express_children=0):
    #Function to Calculate the total cost of a booking, including admission, discounts, rentals, and tour guides.
    adult_total, child_total = calculate_total(adults, children)
    guides_cost = audio_guides(rental)
    if adults + children == 0:
        raise ValueError("Please select at least one ticket.")
    if ticket_type not in PRICES["period_discount"]:
        raise ValueError("Please select a valid visit period.")
    if tour not in PRICES["tour"]:
        raise ValueError("Please select a valid tour duration.")
    family_adults, _extra_adults = family_group(adults, children)
    if family and not family_eligible(adults, children):
        raise ValueError("Family tickets require at least 3 people, including at least 1 child.")
    
    if express:
        express_adults, express_children = adults, children
    _quantity(express_adults)
    _quantity(express_children)
    if express_adults > adults or express_children > children:
        raise ValueError("Express quantities cannot exceed the corresponding ticket quantities.")
    code = discount_code.strip().upper()  # Accept lowercase codes and surrounding spaces.
    if code and code not in DISCOUNT_CODES:
        raise ValueError("Invalid discount code. Try WELCOME10 or LANFANG20.")
    basic_total = _money(adult_total + child_total)
    
    # Standard admission is already included, so add only the express upgrade.
    express_base = express_adults * PRICES["adult"] + express_children * PRICES["child"]
    express_cost = _money(express_base * (PRICES["express_multiplier"] - 1))
    admission = basic_total + express_cost
    period_discount = _money(admission * Decimal(str(PRICES["period_discount"][ticket_type])) / 100)
    admission -= period_discount  # Apply the visit-period discount first.

    #Check if family discount is applicable and calculate the discount amount
    family_discount = _money(0)
    if family:
        family_express_adults = min(express_adults, family_adults)
        family_basic = family_adults * PRICES["adult"] + children * PRICES["child"]
        family_express_base = (family_express_adults * PRICES["adult"]
                               + express_children * PRICES["child"])
        family_admission = _money(family_basic) + _money(
            family_express_base * (PRICES["express_multiplier"] - 1)
        )
        family_period = _money(
            family_admission * Decimal(str(PRICES["period_discount"][ticket_type])) / 100
        )
        family_admission -= family_period
        family_discount = _money(family_admission * Decimal(str(PRICES["family_discount"])) / 100)
    admission -= family_discount  # Family savings apply only to covered visitors.
    code_discount = _money(admission * Decimal(str(DISCOUNT_CODES.get(code, 0))) / 100)
    admission -= code_discount  # Apply the promotional code last.
    guide_count = tour_guides_needed(adults + children) if tour != "None" else 0
    tour_cost = _money(PRICES["tour"][tour] * guide_count)  # Charge for every needed guide.
    return {
        "Adult tickets": _money(adult_total),
        "Child tickets": _money(child_total),
        "Basic ticket total": basic_total,
        "Express upgrade": express_cost,
        "Off-peak discount": -period_discount,
        "Family discount": -family_discount,
        "Discount code savings": -code_discount,
        "Admission total": admission,
        "Audio guides": _money(guides_cost),
        "Group tour": tour_cost,
        "Total to pay": admission + _money(guides_cost) + tour_cost,
    }
