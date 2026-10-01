def can_manage_review_invoices(user):
    """Accounts staff may edit, issue and acknowledge desk-review invoices."""
    return bool(user and user.is_authenticated and (
        user.is_superuser
        or user.groups.filter(name__in=['System Administrator', 'Finance Officer']).exists()
        or user.has_perm('programmes.can_manage_invoices')
        or user.has_perm('programmes.change_programmeassessmentinvoice')
    ))


def can_create_review_invoices(user):
    return can_manage_review_invoices(user) or bool(user and user.is_authenticated and (
        user.groups.filter(name='Head Programme Accreditation').exists()
        or user.has_perm('programmes.add_programmeassessmentinvoice')
    ))
