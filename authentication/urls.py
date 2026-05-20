from django.urls import path
from .views import (
    HealthCheckView,
    ListUsersProfileView,
    SendSignupOTP,
    UpdateAdminProfileView,
    VerifySignupOTP,
    CompleteSignup,
    LoginView,
    CreateFirstSuperuserView,
    CreateAdminView,
    ListStaffView,
    UpdateFCMTokenView,
    UserDashboardView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # ===== CORE SERVICES & APP UTILITIES =====
    path("health/", HealthCheckView.as_view(), name="health-check"),

    # ===== CUSTOMER SIGNUP FLOW (EMAIL OTP BASED) =====
    path("signup/send-otp/", SendSignupOTP.as_view(), name="signup-send-otp"),
    path("signup/verify-otp/", VerifySignupOTP.as_view(), name="signup-verify-otp"),
    path("signup/complete/", CompleteSignup.as_view(), name="signup-complete"),

    # ===== SECURITY PORTAL (AUTHENTICATION & RECOVERY) =====
    path("auth/login/", LoginView.as_view(), name="user-login"),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ===== ROLE-BASED SYSTEM ONBOARDING (RESTRICTED) =====
    # Platform Setup View (Creates main owner)
    path('superuser/create/', CreateFirstSuperuserView.as_view(), name='create-superuser'),
    

    # Admin/Superuser Access: Onboard Urban Service Technicians
    path('staff/list/', ListStaffView.as_view(), name='list-technicians'),

    # ===== PROFILE MANAGEMENT & DETECTOR DASHBOARD ENGINE =====
    path('user/update-fcm-token/', UpdateFCMTokenView.as_view(), name='update-fcm'),
    
    # 🌟 Core Engine: Passes tokens -> returns targeted screen configuration metrics
    path('user/dashboard/', UserDashboardView.as_view(), name='user-dashboard'),

    path('admin/create/', CreateAdminView.as_view(), name='create-admin'),
    path('user/<uuid:user_id>/update/', UpdateAdminProfileView.as_view(), name='user-update'),
    
    # 🌟 NEW CLEAN UNIFIED ENDPOINT RUNS ALL DIRECTORY FILTER CONFIGURATIONS
    path('users/directory/', ListUsersProfileView.as_view(), name='users-directory-profiles'),
]