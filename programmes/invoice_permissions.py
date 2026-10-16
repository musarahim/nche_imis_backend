def can_manage_review_invoices(user):
    """Accounts staff may verify and acknowledge invoice payments."""
    return bool(user and user.is_authenticated and (
        user.is_superuser
        or user.groups.filter(name__in=['System Administrator', 'Finance Officer']).exists()
        or user.has_perm('programmes.can_manage_invoices')
    ))


def can_create_review_invoices(user):
    """The programme head prepares and sends desk-review invoices."""
    return bool(user and user.is_authenticated and (
        user.is_superuser
        or user.groups.filter(name__in=['System Administrator', 'Head Programme Accreditation']).exists()
    ))
