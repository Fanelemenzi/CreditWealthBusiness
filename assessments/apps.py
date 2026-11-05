from django.apps import AppConfig


class AssessmentsConfig(AppConfig):
    name = "assessments"

    def ready(self):
        import assessments.signals  # noqa: F401