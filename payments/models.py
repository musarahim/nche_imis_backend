from accounts.models import User
from django.db import models

# Create your models here.

class PaymentOptions(models.Model):
    name            =   models.CharField(max_length=100)
    description     =   models.TextField(null=True, blank=True)
    created_at      =   models.DateTimeField(auto_now_add=True)
    updated_at      =   models.DateTimeField(auto_now_add=False, null=True, blank=True)
    created_by      =   models.ForeignKey(User, on_delete=models.CASCADE, related_name="payment_option_creator")
    updated_by      =   models.ForeignKey(User, on_delete=models.CASCADE, related_name="payment_option_updater", null=True, blank=True)

    def __str__(self):
        return self.name
    

class ApplicationPRNS(models.Model):
    #application_id              =   models.ForeignKey(Applications, on_delete=models.CASCADE, related_name="related_application_id")
    #related_transaction_type    =   models.ForeignKey(TransactionType, on_delete=models.CASCADE, related_name="related_transaction_type_prns")
    payment_option_id           =   models.ForeignKey(PaymentOptions, on_delete=models.CASCADE, related_name="related_payment_option_id")
    prn                         =   models.CharField(max_length=100)
    status                      =   models.BooleanField(default=False)
    system_status               =   models.BooleanField(default=True)
    pay_request_status          =   models.BooleanField(default=False)
    audit_completed_status      =   models.BooleanField(default=False)
    served_status               =   models.BooleanField(default=False)
    expired                     =   models.BooleanField(default=False)
    banktxnid                   =   models.CharField(max_length=100, null=True, blank=True)
    bank                        =   models.CharField(max_length=100, null=True, blank=True)
    branch                      =   models.CharField(max_length=100, null=True, blank=True)
    payment_date                =   models.DateField(auto_now_add=False, null=True, blank=True)
    created_at                  =   models.DateField(auto_now_add=True)

    def __str__(self):
        return self.prn
    


class PRNCallIns(models.Model):
    prn             =   models.CharField(max_length=100)
    created_at      =   models.DateTimeField(auto_now_add=True)
    status          =   models.BooleanField(default=True)

class PaymentRequests(models.Model):
    related_prn             =   models.ForeignKey(ApplicationPRNS, on_delete=models.CASCADE, related_name="related_prn_payment_request")
    internal_transaction_id =   models.CharField(max_length=100) 
    mobile_number            =   models.CharField(max_length=12, null=True, blank=True)
    external_transaction_id =   models.CharField(max_length=100)
    return_transaction_id   =   models.CharField(max_length=100, null=True, blank=True)
    pay_request_status      =   models.BooleanField(default=False)
    request_response        =   models.TextField(null=True, blank=True)
    response_status         =   models.BooleanField(default=True)
    updated_at              =   models.DateTimeField(auto_now_add=False, null=True, blank=True)
    created_at              =   models.DateTimeField(auto_now_add=True)

class PaymentRequestCallbacks(models.Model):
    prn                     =   models.ForeignKey(ApplicationPRNS, on_delete=models.CASCADE, related_name="related_prn_payment_request_callback")
    ura_status              =   models.CharField(max_length=40)
    mobilemoney_post_date   =   models.DateTimeField(auto_now_add=False, null=True, blank=True)
    mm_transaction_id       =   models.CharField(max_length=100)
    ura_post_date           =   models.DateTimeField(auto_now_add=False, null=True, blank=True)
    date_created            =   models.DateTimeField(auto_now_add=False, null=True, blank=True)
    overall_status          =   models.CharField(max_length=20)
    last_post_message       =   models.CharField(max_length=20)
    internal_reference      =   models.CharField(max_length=20)
    external_reference      =   models.CharField(max_length=20)
    amount                  =   models.DecimalField(max_digits=20, decimal_places=2)
    created_at              =   models.DateTimeField(auto_now_add=True)