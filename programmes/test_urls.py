from rest_framework.routers import DefaultRouter
from .review_invoice_views import ProgrammeAssessmentInvoiceViewset
from .views import ProgrammeAccreditationViewset, ProgrammeInvoiceViewset, ProgramViewset

router = DefaultRouter()
router.register('invoices', ProgrammeAssessmentInvoiceViewset, basename='review-invoice')
router.register('programme-accreditation', ProgrammeAccreditationViewset, basename='programme-accreditation')
router.register('institution-programmes', ProgramViewset, basename='programs')
router.register('programme-invoices', ProgrammeInvoiceViewset, basename='programme-invoices')
urlpatterns = router.urls
