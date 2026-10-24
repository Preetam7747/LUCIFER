def analyze_complaint(title, description):
    text = f"{title} {description}".lower()

    categories = {
        "maintenance": [
            "fan",
            "light",
            "electricity",
            "water",
            "tap",
            "leak",
            "door",
            "repair"
        ],
        "cleanliness": [
            "clean",
            "dirty",
            "garbage",
            "dust",
            "bathroom"
        ],
        "mess": [
            "food",
            "mess",
            "breakfast",
            "lunch",
            "dinner",
            "meal"
        ],
        "security": [
            "security",
            "visitor",
            "lock",
            "unsafe"
        ]
    }

    detected_category = "other"

    for category, keywords in categories.items():
        if any(word in text for word in keywords):
            detected_category = category
            break

    return {
        "category": detected_category,
        "summary": f"Complaint detected as {detected_category}.",
        "priority": detect_priority(text)
    }


def detect_priority(text):
    urgent_words = [
        "urgent",
        "emergency",
        "danger",
        "fire",
        "medical",
        "security"
    ]

    if any(word in text for word in urgent_words):
        return "high"

    return "normal"


def suggest_complaint_category(title, description):
    result = analyze_complaint(title, description)
    return result["category"]