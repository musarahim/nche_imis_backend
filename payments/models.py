from accounts.models import User
from django.db import models

# Create your models here.
    
class PaymentCode(models.Model):
    '''Model to store payment codes and their details'''
    STATE_CHOICES = (
        (True, u'Yes'),
        (False, u'No'),
    )
    code = models.CharField(max_length=100, unique=True)
    payment_tax_head = models.CharField(max_length=100)
    available = models.BooleanField(default=True, choices=STATE_CHOICES)
    base_value = models.IntegerField()
    base_value_currency = models.CharField(max_length=100, null=True)
    tax_head_currency = models.CharField(max_length=100, null=True)
    #fees_per_unit = models.DecimalField(decimal_places=2, max_digits=10, null=True)

    def __str__(self) -> str:
        return self.code
    

class ApplicationPRNS(models.Model):

    '''prn request model to store URA PRN details'''
    amount =  models.DecimalField(max_digits=20, decimal_places=2, null=True)
    assessmentDate = models.DateTimeField(null=True, blank=True)
    paymentType = models.CharField(max_length=100, null=True, blank=True)# DT
    # map application ID to reference number when generating PRN
    referenceNo = models.CharField(max_length=100, blank=True, null=True) # ReferenceNo
    tin = models.CharField(max_length=100, null=True, blank=True)
    srcSystem = models.CharField(max_length=100, null=True, blank=True)
    taxHead = models.CharField(max_length=100, null=True, blank=True)
    taxSubHead = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    taxPayerName = models.CharField(max_length=100, null=True, blank=True)
    plot = models.CharField(max_length=100, null=True, blank=True)
    buildingName = models.CharField(max_length=100, null=True, blank=True)
    street = models.CharField(max_length=100, null=True, blank=True)
    tradeCentre = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    county = models.CharField(max_length=100, null=True, blank=True)
    subCounty = models.CharField(max_length=100, null=True, blank=True)
    parish = models.CharField(max_length=100, null=True, blank=True)
    village = models.CharField(max_length=100, null=True, blank=True)
    localCouncil = models.CharField(max_length=100, null=True, blank=True)
    contactNo = models.CharField(max_length=100, null=True, blank=True)
    paymentPeriod = models.CharField(max_length=100, null=True, blank=True)
    expiryDays = models.CharField(max_length=100, null=True, blank=True)
    mobileMoneyNumber = models.CharField(max_length=100, null=True, blank=True)
    mobileNo = models.CharField(max_length=100, null=True, blank=True)
    # PRN response data structure
    expiryDate = models.DateField(null=True, blank=True) 
    statusCode = models.CharField(max_length=10, null=True, blank=True)
    statusDesc = models.CharField(max_length=100, null=True, blank=True)
    searchCode = models.CharField(max_length=100, null=True, blank=True)
    prn = models.CharField(max_length=100, null=True, blank=True)
    prn_reconciled = models.BooleanField(default=False)


    def __str__(self):
        return self.prn
    



