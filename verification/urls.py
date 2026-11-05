from django.urls import path

from assessments.views import SMSWebhookView

urlpatterns = [
    path("", SMSWebhookView.as_view(), name="sms-webhook"),
]
