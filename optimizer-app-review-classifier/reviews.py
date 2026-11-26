"""Fictional Pebblepad (a budgeting app) store reviews, labeled by intent."""

LABELS = [
    "bug_report",
    "feature_request",
    "praise",
    "billing_complaint",
    "usability_confusion",
]

# (review text, intent label). A few are deliberately tricky: praise that
# ends in a wish, a billing gripe caused by a bug, confusion that sounds like a bug.
REVIEWS: list[tuple[str, str]] = [
    ("App closes itself every time I open the Reports tab on my Pixel 7.", "bug_report"),
    ("Synced my bank yesterday and now every transaction shows up twice.", "bug_report"),
    ("Dark mode flips back to light after each restart. Please fix!", "bug_report"),
    ("The budget total says $0 after I edit a category, until I force-quit the app.", "bug_report"),
    ("Would love a shared household budget so my partner can add expenses too.", "feature_request"),
    ("Please add CSV export. I need my data in a spreadsheet for taxes.", "feature_request"),
    ("Any chance of a home-screen widget showing what is left this week?", "feature_request"),
    ("Great app, but it badly needs recurring-transaction support. Adding rent by hand every month is a drag.", "feature_request"),
    ("Finally an app that makes me enjoy checking my spending. Five stars, no notes.", "praise"),
    ("The envelope view clicked for me instantly. Paid off my card in four months!", "praise"),
    ("Clean, fast, and the weekly summary is genuinely motivating. Thank you, team.", "praise"),
    ("Best budgeting app I have tried, and I have tried a lot.", "praise"),
    ("Charged $59.99 for the annual plan even though the listing said $39.99.", "billing_complaint"),
    ("I cancelled my trial on day 5 and was billed anyway. Refund requested twice, no reply.", "billing_complaint"),
    ("Paywalling basic category limits after the update is a cash grab. Not paying $8 a month for that.", "billing_complaint"),
    ("Premium renewed at a higher price with zero warning email.", "billing_complaint"),
    ("I can't figure out how to move money between envelopes. Where is that button?", "usability_confusion"),
    ("What is the difference between 'planned' and 'budgeted'? The labels make no sense to me.", "usability_confusion"),
    ("Spent twenty minutes hunting for how to delete a category. The menu is a maze.", "usability_confusion"),
    ("Not sure how to mark a transaction as split. Is it supposed to be a long-press?", "usability_confusion"),
]
