from .database import get_connection

def seed():
    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM events"
        ).fetchone()["n"]

        if count:
            return

        # Seed Events
        conn.executemany(
            """
            INSERT INTO events
            (
                name,
                college,
                event_type,
                event_date,
                start_time,
                duration_hours,
                expected_attendees,
                meal_period,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "TechNova Campus Fest",
                    "JVM Mehta College",
                    "College Fest",
                    "2026-12-12",
                    "11:00",
                    7,
                    850,
                    "Lunch",
                    "Scheduled"
                ),
                (
                    "InnovateX Hackathon",
                    "JVM Mehta College",
                    "Hackathon",
                    "2026-12-18",
                    "09:00",
                    12,
                    320,
                    "All-day",
                    "Scheduled"
                ),
                (
                    "Freshers Connect",
                    "North Campus College",
                    "Cultural Event",
                    "2027-01-08",
                    "16:00",
                    4,
                    500,
                    "Snacks",
                    "Scheduled"
                ),
            ],
        )

        # Seed Vendors
        conn.executemany(
            """
            INSERT INTO vendors
            (name, cuisine, location, rating, active)
            VALUES (?, ?, ?, ?, 1)
            """,
            [
                ("Campus Kitchen Co.", "Indian", "Main Gate Food Court", 4.6),
                ("Wrap & Roll Studio", "Fast Food", "West Gate", 4.4),
                ("Green Bowl Collective", "Healthy", "Library Lane", 4.7),
                ("Chai Junction", "Beverages", "Auditorium Plaza", 4.3),
            ],
        )

        # Seed Menu Items
        conn.executemany(
            """
            INSERT INTO menu_items
            (vendor_id, name, category, price, available_qty)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (1, "Paneer Rice Bowl", "Meals", 110, 180),
                (1, "Veg Biryani Box", "Meals", 95, 150),
                (2, "Paneer Kathi Roll", "Snacks", 85, 120),
                (2, "Classic Veg Burger", "Snacks", 75, 100),
                (3, "Protein Power Bowl", "Healthy", 135, 80),
                (3, "Sprout & Corn Salad", "Healthy", 90, 80),
                (4, "Masala Chai", "Beverages", 25, 300),
                (4, "Cold Coffee", "Beverages", 65, 180),
            ],
        )

        print("Swiggy EventFuel database seeded successfully!")
