from django.urls import path
from .views import ChangePasswordView,MeView,RegisterView

urlpatterns = [

    # # 1. Токены (Логин и Refresh) — если используете JWT
    # path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),  # POST: login (email + password -> access + refresh)
    # path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"), # POS


    path("register/",RegisterView.as_view(),name="register"),
    path("me/",MeView.as_view(),name="me"),
    path("change-password/",ChangePasswordView.as_view(),name="change-password"),
]