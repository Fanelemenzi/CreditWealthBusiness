from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from accounts.serializers import BusinessOwnerSerializer, BusinessOwnerUpdateSerializer


class MeView(RetrieveUpdateAPIView):
    """
    GET   /api/auth/me/   → return the current user's business profile.
    PATCH /api/auth/me/   → update profile fields (phone, national_id, etc.).

    Authentication is done by FirebaseAuthentication — the client must include
    `Authorization: Bearer <Firebase ID token>` on every request.

    There are no register or login endpoints here: sign-up, login (email/password
    or Google), logout, password reset, and email verification are all handled
    client-side through the Firebase SDK.
    """

    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]  # no PUT

    def get_serializer_class(self):
        if self.request.method in ("PATCH",):
            return BusinessOwnerUpdateSerializer
        return BusinessOwnerSerializer

    def get_object(self):
        return self.request.user
