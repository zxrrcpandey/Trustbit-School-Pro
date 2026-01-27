app_name = "trustbit_school_pro"
app_title = "Trustbit School Pro"
app_publisher = "Trustbit Software"
app_description = "Book Sample Management for Schools - Track samples from warehouse to schools and back"
app_email = "info@trustbit.com"
app_license = "MIT"
required_apps = ["frappe", "erpnext"]

# Document Events
doc_events = {
    "Vehicle": {
        "after_insert": "trustbit_school_pro.trustbit_school_pro.doctype.vehicle.vehicle.create_vehicle_warehouse",
    },
}

# Fixtures - Custom Fields for Stock Entry linking
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["module", "=", "Trustbit School Pro"]],
    },
]

# Custom Fields to be added to Item Master
# These will be created via fixtures or install script
"""
Custom Fields for Item:
1. custom_is_sample_book (Check) - Is this a sample book?
2. custom_subject (Data) - Subject (Math, Science, etc.)
3. custom_class_grade (Data) - Class/Grade (1, 2, 3... 12)
4. custom_author (Data) - Author name
5. custom_edition_year (Data) - Edition/Year
6. custom_isbn (Data) - ISBN number
"""

# Includes in the Website
# Include js, css files in header of web template
# web_include_css = "/assets/trustbit_school_pro/css/trustbit_school_pro.css"
# web_include_js = "/assets/trustbit_school_pro/js/trustbit_school_pro.js"

# Include js, css files in header of desk
app_include_css = "/assets/trustbit_school_pro/css/trustbit_school_pro.css"
app_include_js = "/assets/trustbit_school_pro/js/trustbit_school_pro.js"

# Desk Notifications
# notification_config = "trustbit_school_pro.notifications.get_notification_config"

# Default print format
# default_print_format = "Trustbit School Pro"

# Installation
after_install = "trustbit_school_pro.install.after_install"
before_uninstall = "trustbit_school_pro.uninstall.before_uninstall"

# Scheduled Tasks
# scheduler_events = {
#     "daily": [
#         "trustbit_school_pro.tasks.daily"
#     ],
# }
