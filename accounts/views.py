from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import BusinessOwnerSerializer, RegistrationSerializer


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer


class CurrentUserView(APIView):
    def get(self, request):
        return Response(BusinessOwnerSerializer(request.user).data)
