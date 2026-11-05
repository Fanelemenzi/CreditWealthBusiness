from django.urls import path

from assessments.views import (
    AssessmentListView,
    AssessmentResultView,
    AssessmentSubmitView,
)

urlpatterns = [
    path("", AssessmentListView.as_view(), name="assessment-list"),
    path("submit/", AssessmentSubmitView.as_view(), name="assessment-submit"),
    path("<uuid:pk>/result/", AssessmentResultView.as_view(), name="assessment-result"),
]
