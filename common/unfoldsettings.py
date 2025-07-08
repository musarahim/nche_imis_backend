import os

from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "UNCHE IMIS",
    "SITE_HEADER": "UNCHE IMIS",
    "SITE_SUBHEADER": "Admin Portal",
    "SITE_DROPDOWN": [
        {
            "icon": "diamond",
            "title": _("Home"),
            "link": os.environ.get("DOMAIN", reverse_lazy("admin:index")),
        },
        
    ],
    "SITE_URL": "/",
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
            "href": lambda request: static("favicon.svg"),
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
        lambda request: static("css/style.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/script.js"),
    ],
    "BORDER_RADIUS": "6px",
    "COLORS": {
        "base": {
            "50": "249, 250, 251", 
            "100": "243, 244, 246", 
            "200": "229, 231, 235",
            "300": "209, 213, 219",
            "400": "156, 163, 175", 
            "500": "107, 114, 128", 
            "600": "75, 85, 99",
            "700": "55, 65, 81",
            "800": "31, 41, 55",
            "900": "17, 24, 39",   
            "950": "3, 7, 18"      
        },
        "primary": {
            "50": "229, 237, 247",   
            "100": "194, 214, 236",  
            "200": "148, 183, 222",  
            "300": "102, 153, 208",  
            "400": "56, 124, 194",  
            "500": "26, 75, 125",    
            "600": "20, 58, 97",  
            "700": "15, 43, 72",  
            "800": "10, 29, 48",    
            "900": "5, 14, 24",    
            "950": "2, 7, 12"   
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
        "show_search": False,  # Search in applications and models names
        "show_all_applications": False,  # Dropdown with all applications and models
        "navigation": [
            {
                "title": _("Navigation"),
                "separator": True,  # Top border
                "collapsible": True,  # Collapsible group of links
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",  # Supported icon set: https://fonts.google.com/icons
                        "link": reverse_lazy("admin:index"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Users"),
                        "icon": "people",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                    {
                        "title": _("Groups"),
                        "icon": "groups",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    }
                ],
            },
        ],
    },
    "TABS": [
       
    ],
}




def badge_callback(request):
    return 3
