# gender choices
GENDER=(
    ('male', 'Male'),
    ('female', 'Female'),
)

# marital status choices
MARITAL_STATUS=(
    ('single', 'Single'),
    ('married', 'Married'),
    ('divorced', 'Divorced'),
    ('widow', 'Widow'),
    ('widower', 'Widower'),
    ('seperated', 'Seperated'),
)

# parent status
PARENT_STATUS=(
    ('alive', 'Alive'),
    ('deceased', 'Deceased'),
    
)

PASSPORT_TYPE_CHOICES= [
        ('ordinary', 'Ordinary'),
        ('service', 'Service/Official'),
        ('diplomatic', 'Diplomatic'),
]
BANK_ACCOUNT_TYPE_CHOICES = [
    ('savings', 'Savings'),
    ('current', 'Current'),
    ('fixed_deposit', 'Fixed Deposit'),
    ('joint_account', 'Joint Account'),
]


# blood group choices
BLOOD_GROUP=(
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
)

LEASE_RENTED=(
        ('lease', 'Lease'),
        ('rent', 'Rent'),
    )

PROGRAMME_LEVELS = [
    ('certificate', 'Certificate'),
    ('diploma', 'Diploma'),
    ('bachelor', 'Bachelors'),
    ('post_graduate_diploma', 'Post Graduate Diploma'),
    ('masters', 'Masters'),
    ('phd', 'PhD'),
    ('other', 'Other'),
]

STATUS_CHOICES = (
        # Initial stages
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('prelim_review', 'Under Preliminary Review'),
        ('prelim_feedback', 'Preliminary Feedback Issued'),

        # Vetting stages
        ('vetting_scheduled', 'Scheduled for Vetting'),
        ('vetting_in_progress', 'Vetting in Progress'),
        ('vetting_feedback', 'Vetting Decision Issued'),

        # Administrative visit to verify land/infrastructure
        ('admin_visit_pending', 'Administrative Visit Pending'),
        ('admin_visit_done', 'Administrative Visit Completed'),

        # NCHE organs review (Directorate, Management, QAAC, Council)
        ('under_directorate_review', 'Under Directorate Review'),
        ('under_management_review', 'Under Management Review'),
        ('under_qaac_review', 'Under QAAC Review'),
        ('under_council_review', 'Under Council Review'),

        # Council decision and fees
        ('approved_pending_fees', 'Approved – Pending Fee Payment'),
        ('fees_invoiced', 'Fees Invoiced'),
        ('fees_paid', 'Fees Paid – Certificate Processing'),

        # Certificate issuance / completion
        ('certificate_ready', 'Certificate Ready for Collection'),
        ('completed', 'Completed – LIA Issued'),

        # On-hold / negative outcomes
        ('on_hold_requirements', 'On Hold – Requirements Not Met'),
        ('on_hold_non_compliance', 'On Hold – Non-Compliance Issues'),
        ('deferred', 'Deferred'),
        ('rejected', 'Rejected / Not Approved'),
    )