import os

from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "UNCHE IMIS",
    "SITE_HEADER": "UNCHE IMIS",
    "SITE_SUBHEADER": "Portal",
    "SITE_DROPDOWN": [
        {
            "icon": "diamond",
            "title": _("Home"),
            "link": os.environ.get("DOMAIN", reverse_lazy("admin:index")),
        },
        
    ],
        "COMMAND": {
        "search_models": True,  # Default: False
        "search_callback": "utils.search_callback",
        "show_history": True,  # Enable history
    },
    "SITE_URL": "/portal",
    # "SITE_ICON": lambda request: static("icon.svg"),  # both modes, optimise for 32px height
    "SITE_ICON": {
        "light": lambda request: static("icon-light.svg"),  # light mode
        "dark": lambda request: static("icon-dark.svg"),  # dark mode
    },
    # "SITE_LOGO": lambda request: static("logo.svg"),  # both modes, optimise for 32px height
    "SITE_LOGO": {
        "light": lambda request: static("images/logo.png"),  # light mode
        "dark": lambda request: static("images/logo.png"),  # dark mode
    },
    "SITE_SYMBOL": "speed",  # symbol from icon set
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("images/favicon.ico"),
        },
    ],
    "SHOW_HISTORY": True, # show/hide "History" button, default: True
    "SHOW_VIEW_ON_SITE": True, # show/hide "View on site" button, default: True
    "SHOW_BACK_BUTTON": False, # show/hide "Back" button on changeform in header, default: False
    #"ENVIRONMENT": "sample_app.environment_callback", # environment name in header
    #"ENVIRONMENT_TITLE_PREFIX": "sample_app.environment_title_prefix_callback", # environment name prefix in title tag
    #"DASHBOARD_CALLBACK": "sample_app.dashboard_callback", # prepare custom variables for index template,
    #"THEME": "dark", # Force theme: "dark" or "light". Will disable theme switcher
    "LOGIN": {
        "image": lambda request: static("images/login_bg.png"),
        "redirect_after": lambda request: reverse_lazy("admin:index"),
    },
    "STYLES": [
        lambda request: static("css/styles.css"),
    ],
    # "SCRIPTS": [
    #     lambda request: static("js/script.js"),
    # ],
    "BORDER_RADIUS": "6px",
    "COLORS": {
        "base": {
            "50": "oklch(98.5% .002 247.839)",
            "100": "oklch(96.7% .003 264.542)",
            "200": "oklch(92.8% .006 264.531)",
            "300": "oklch(87.2% .01 258.338)",
            "400": "oklch(70.7% .022 261.325)",
            "500": "oklch(55.1% .027 264.364)",
            "600": "oklch(44.6% .03 256.802)",
            "700": "oklch(37.3% .034 259.733)",
            "800": "oklch(27.8% .033 256.848)",
            "900": "oklch(21% .034 264.665)",
            "950": "oklch(13% .028 261.692)",
            
        },
        "primary": {
           "50":  "oklch(0.985 0.015 248.3)",
            "100": "oklch(0.940 0.025 248.3)",
            "200": "oklch(0.870 0.040 248.3)",
            "300": "oklch(0.750 0.055 248.3)",
            "400": "oklch(0.620 0.065 248.3)",
            "500": "oklch(0.370 0.065 248.3)",
            "600": "oklch(0.320 0.060 248.3)",
            "700": "oklch(0.260 0.055 248.3)",
            "800": "oklch(0.200 0.045 248.3)",
            "900": "oklch(0.150 0.035 248.3)",
            "950": "oklch(0.5500 0.1700 38)"
        },
        "secondary": {
            "50": "oklch(0.985 0.015 248.3)",
            "100": "oklch(0.940 0.025 248.3)",
            "200": "oklch(0.870 0.040 248.3)",
            "300": "oklch(0.750 0.055 248.3)",
            "400": "oklch(0.620 0.065 248.3)",
            "500": "oklch(0.370 0.065 248.3)",
            "600": "oklch(0.320 0.060 248.3)",
            "700": "oklch(0.260 0.055 248.3)",
            "800": "oklch(0.200 0.045 248.3)",
            "900": "oklch(0.150 0.035 248.3)",
            "950": "oklch(0.100 0.025 248.3)"
        },
        "font": {
            "subtle-light": "var(--color-base-600)",  # text-base-500
            "subtle-dark": "var(--color-base-500)",  # text-base-400
            "default-light": "var(--color-base-700)",  # text-base-600
            "default-dark": "var(--color-base-400)",  # text-base-300
            "important-light": "var(--color-base-950)",  # text-base-900
            "important-dark": "var(--color-base-200)",  # text-base-100
        },
       
   
    },
    "EXTENSIONS": {
    },
    "SIDEBAR": {
    "show_search": True,
    "show_all_applications": False,
    "navigation": [
        # GROUP 1: Main Navigation Links
        {
            "title": None,
            "separator": True,
            "items": [
                {
                    "title": _("Dashboard"),
                    "icon": "dashboard",
                    "link": reverse_lazy("admin:index"),
                    "permission": lambda request: request.user.is_superuser,
                },
               
            ],
        },

        {
            "title": _("Users"),
            "icon": "manage_accounts",
            "collapsible": True,
            "permission": lambda request: request.user.is_superuser,
            "items": [
                {
                    "title": _("Users"),
                    "link": reverse_lazy("admin:accounts_user_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "manage_accounts",
                },
                {
                    "title": _("Groups"),
                    "link": reverse_lazy("admin:auth_group_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "manage_accounts",
                },
            ],
        },

        # GROUP 2: The Configurations Dropdown
        {
            "title": _("Configurations"),
            "icon": "manage_accounts",
            "collapsible": True,
            "permission": lambda request: request.user.is_superuser,
            "items": [
                 {
                    "title": _("Regions"),
                    "link": reverse_lazy("admin:common_region_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "location_on",
                },  
                {
                    "title": _("Districts"),
                    "link": reverse_lazy("admin:common_district_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "location_on",
                },   
                {
                    "title": _("Counties"),
                    "link": reverse_lazy("admin:common_county_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "location_on",
                },  
                {
                    "title": _("Sub Counties"),
                    "link": reverse_lazy("admin:common_subcounty_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "location_on",
                },  
                {
                    "title": _("Parishes"),
                    "link": reverse_lazy("admin:common_parish_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "location_on",
                },  
                {
                    "title": _("Villages"),
                    "link": reverse_lazy("admin:common_village_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "location_on",
                },  
                         
                  {
                    "title": _("Education Levels"),
                    "link": reverse_lazy("admin:common_educationlevel_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "cast_for_education",
                },
                  {
                    "title": _("Titles"),
                    "link": reverse_lazy("admin:common_title_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "title",
                },
                 {
                    "title": _("Tribes"),
                    "link": reverse_lazy("admin:common_tribe_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "people",
                },
                  {
                    "title": _("Religions"),
                    "link": reverse_lazy("admin:common_religion_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "folded_hands",
                },                  
                {
                    "title": _("Nationalities"),
                    "link": reverse_lazy("admin:common_nationality_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "public",
                },
                
                # ... add your other uncommented configuration items here
            ],
        },

        {
            "title": _("Institutions"),
            "icon": "manage_accounts",
            "collapsible": True,
            "permission": lambda request: request.user.is_superuser,
            "items": [
                {
                    "title": _("Institutions"),
                    "link": reverse_lazy("admin:institutions_institution_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "apartment",
                },
               
                
                # ... add your other uncommented configuration items here
            ],
        },
        {
            "title": _("Licenses"),
            "icon": "contract",
            "collapsible": True,
            "permission": lambda request: request.user.is_superuser,
            "items": [
                {
                    "title": _("License Types"),
                    "link": reverse_lazy("admin:license_licensetype_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "rule_settings",
                },
                {
                    "title": _("Intrim Authority"),
                    "link": reverse_lazy("admin:license_intrimauthority_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "contract",
                },
                {
                    "title": _("University Provisional License"),
                    "link": reverse_lazy("admin:license_universityprovisionallicense_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "school",
                },
                {
                    "title": _("University Grant Charter Applications"),
                    "link": reverse_lazy("admin:license_charterapplication_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "school",
                },
                
                # ... add your other uncommented configuration items here
            ],
        },
        {
            "title": _("Licenses"),
            "icon": "contract",
            "collapsible": True,
            "permission": lambda request: request.user.is_superuser,
            "items": [
                {
                    "title": _("License Types"),
                    "link": reverse_lazy("admin:license_licensetype_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "rule_settings",
                },
                {
                    "title": _("Intrim Authority"),
                    "link": reverse_lazy("admin:license_intrimauthority_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "contract",
                },
                
                # ... add your other uncommented configuration items here
            ],
        },
        {
            "title": _("Human Resource"),
            "icon": "people",
            "collapsible": True,
            "permission": lambda request: request.user.is_superuser,
            "items": [
                {
                    "title": _("Directorates"),
                    "link": reverse_lazy("admin:hr_directorate_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "apartment",
                },
                {
                    "title": _("Departments"),
                    "link": reverse_lazy("admin:hr_department_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "location_city",
                },
                 {
                    "title": _("Designations"),
                    "link": reverse_lazy("admin:hr_designation_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "work",
                },
                 {
                    "title": _("Employees"),
                    "link": reverse_lazy("admin:hr_employee_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                    "icon": "people",
                },
                
                # ... add your other uncommented configuration items here
            ],
        },

    ],
},
  
    "TABS": [
       
    ],
}




def badge_callback(request):
    return 3
