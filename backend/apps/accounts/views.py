from django.shortcuts import render

# pyrefly: ignore [missing-import]
from rest_framework import generics, status
# pyrefly: ignore [missing-import]
from rest_framework.permissions import AllowAny, IsAuthenticated
# pyrefly: ignore [missing-import]
from rest_framework.response import Response

from .serializers import (
    ChangePasswordSerializer,
    UserRegisterSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]


class MeView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(
            serializer.validated_data["new_password"]
        )
        user.save(update_fields=["password"])

        return Response(
            {"detail": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )
