import random
import logging
from django.contrib.auth import authenticate
from django.db.models import Q
from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from core.utils.email import send_otp_email
from core.utils.otp import generate_otp
from core.utils.permissions import IsAdminOrSuperuser, IsSuperuser
from core.utils.response import error_response, success_response
from .models import CustomUser, OTP, RecoveryContact, UserProfile
from .serializers import *
from django.db import transaction
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)

# 1. HEALTH CHECK VIEW
class HealthCheckView(APIView):
    authentication_classes = [] 
    permission_classes = [] 
    def get(self, request):
        return Response({"status": "ok", "message": "System Core Engine is running 🚀"}, status=status.HTTP_200_OK)


class CreateFirstSuperuserView(APIView):
    """ONLY ONCE: Creates the root platform owner/superuser with optional profile image binary mapping"""
    permission_classes = [AllowAny]

    def post(self, request):
        # Integrity Guard: Action forbidden if superuser already exists
        if CustomUser.objects.filter(role='superuser').exists():
            return error_response("Superuser mapping locked. Already exists.", 403)

        # Deserialize and Validate multipart/form data payload
        serializer = CreateSuperuserSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, 400)

        # Extract Clean Validated Identity Fields
        first_name = serializer.validated_data['first_name'].strip()
        last_name = serializer.validated_data['last_name'].strip()
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # Combine names for Core CustomUser.name mapping
        full_name = f"{first_name} {last_name}".strip()

        # Automatic Unique Username Generation Matrix
        username = email.split('@')[0]
        while CustomUser.objects.filter(username=username).exists():
            username = f"{email.split('@')[0]}{random.randint(10, 99)}"

        # 🌟 CATCH IMAGE FILE FROM FORM-DATA STREAM (Optional logic)
        profile_img = request.FILES.get('profile_image', None)

        try:
            # 🚀 Save parameters to Core Auth Table
            user = CustomUser.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                name=full_name,
                role='superuser',
                is_verified=True,
                is_password_set=True
            )

            # 🚀 Save profile attachments into the new UserProfile Specs Model
            # Agar image empty aayi (None) toh DB table blank safely persist ho jayega.
            UserProfile.objects.create(
                user=user,
                profile_image=profile_img
            )

            # Generate absolute media path URI structure for Flutter clean loading layout mapping
            absolute_image_url = None
            if user.profile.profile_image:
                absolute_image_url = request.build_absolute_uri(user.profile.profile_image.url)

            return success_response(
                "Root Platform Superuser instantiated successfully.",
                data={
                    "user_id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "compiled_name": user.name,
                    "role": user.role,
                    "profile_image_path": absolute_image_url
                },
                status_code=201
            )

        except Exception as e:
            return error_response(f"Internal Database Transaction Fault: {str(e)}", 500)
  


class CreateAdminView(APIView):
    """FINANCIAL ERP COMPONENT: Onboards verified admin managers with full profile specification maps"""
    permission_classes = [IsSuperuser]

    def post(self, request):
        serializer = CreateAdminSerializer(data=request.data)
        if not serializer.is_valid():
            print("🚨 DRF SERIALIZATION REJECTION LIST:", serializer.errors)
            return error_response(serializer.errors, 400)

        # 2. Extract Clean Sanitized Fields
        first_name = serializer.validated_data['first_name'].strip()
        last_name = serializer.validated_data['last_name'].strip()
        email = serializer.validated_data['email'].strip()
        password = serializer.validated_data['password']
        phone_number = serializer.validated_data.get('phone_number', '').strip()

        # Combine variables to form full corporate accounting ledger names representation
        compiled_full_name = f"{first_name} {last_name}".strip()

        # 3. Unique Runtime Username Allocation Engine
        username = email.split('@')[0]
        while CustomUser.objects.filter(username=username).exists():
            username = f"{email.split('@')[0]}{random.randint(10, 99)}"

        try:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                phone_number=phone_number if phone_number != "" else None,
                password=password,
                first_name=first_name,
                last_name=last_name,
                name=compiled_full_name,
                role='admin',
                created_by=request.user,
                is_verified=True,
                is_password_set=True
            )

            raw_age = serializer.validated_data.get('age', '').strip()
            clean_age = int(raw_age) if raw_age.isdigit() else None

            # Validate gender input strings matches choice parameters constraints
            raw_gender = serializer.validated_data.get('gender', 'MALE').upper().strip()
            clean_gender = raw_gender if raw_gender in ['MALE', 'FEMALE', 'OTHER'] else 'MALE'

            # Catch profile picture multi-part files streams buffers safely
            profile_img = request.FILES.get('profile_image', None)

            # 🚀 Instantiating UserProfile table tracking entries row safely
            UserProfile.objects.create(
                user=user,
                profile_image=profile_img,
                age=clean_age,
                gender=clean_gender
            )

            # 5. Build native verification nodes for Recovery logs references
            if user.email:
                RecoveryContact.objects.create(
                    user=user, 
                    contact_type="email", 
                    contact_value=user.email, 
                    is_verified=True
                )

            return success_response(
                "Operational Admin Profile created successfully.", 
                data={"user_id": str(user.id), "role": user.role, "username": user.username},
                status_code=201
            )

        except Exception as e:
            # Catch internal model logic violations crashes cleanly
            print("🚨 DATABASE TRANSACTION TRANSACTION CRASH DETAIL:", str(e))
            return error_response(f"Internal Database Transaction Fault: {str(e)}", 500)


# 4. SIGNUP: SEND OTP VIEW
class SendSignupOTP(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        data = request.data.copy()
        email_input = data.get("email")
        if not email_input: return error_response("Email configuration mapping required.", 400)
        if CustomUser.objects.filter(email=email_input).exists(): return error_response("Email index profile already exists.", 400)

        base_username = email_input.split('@')[0]
        username = base_username
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{random.randint(10, 99)}"
        data["username"] = username

        serializer = SignupSendOTPSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        otp = generate_otp()
        OTP.objects.update_or_create(email=email_input, purpose="signup", defaults={"otp": otp, "verified": False})
        send_otp_email(email_input, otp)
        return success_response("Registration token verification OTP processed to data maps.")





class UpdateAdminProfileView(APIView):
    """FINANCIAL CONTEXT ENGINE: Modifies administrative credentials and specifications registries"""
    permission_classes = [IsSuperuser]

    @transaction.atomic
    def put(self, request, user_id):
        # 1. Look up user identity safely via explicit route UUID match string parameter
        user = get_object_or_404(CustomUser, id=user_id)
        
        # 2. Bind payload data matrix into configuration validation core pipeline
        serializer = UpdateAdminProfileSerializer(data=request.data)
        if not serializer.is_valid():
            print("🚨 DRF MODIFICATION FAILURE ERRORS:", serializer.errors)
            return error_response(serializer.errors, 400)

        try:
            # 3. Step 1: Update CustomUser Core Table Data Context
            if 'name' in serializer.validated_data and serializer.validated_data['name']:
                user.name = serializer.validated_data['name'].strip()
                
                # AbstractUser Fallbacks matching parameters splits
                name_parts = user.name.split(' ')
                user.first_name = name_parts[0]
                user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            
            # Encrypt password safely using Django set_password matrix if present
            plain_password = serializer.validated_data.get('password', '').strip()
            if plain_password:
                user.set_password(plain_password)
                user.is_password_set = True
                
            user.save()

            # 4. Step 2: Synchronize Separated UserProfile Extended Specs Row
            # Fetch or instantiate empty profile container row seamlessly to prevent integrity exception crashes
            profile, created = UserProfile.objects.get_or_create(user=user)

            raw_age = serializer.validated_data.get('age', '').strip()
            if raw_age:
                profile.age = int(raw_age)
            
            # Optional: Dynamic profile profile picture extraction middleware interceptor
            if 'profile_image' in request.FILES:
                profile.profile_image = request.FILES['profile_image']

            profile.save()

            return success_response(
                "Profile Registries and parameters synced successfully.",
                data={
                    "user_id": str(user.id),
                    "username": user.username,
                    "updated_name": user.name,
                    "profile_age_spec": profile.age
                },
                status_code=200
            )

        except Exception as e:
            print("🚨 CRITICAL SYSTEM DATABASE MODIFICATION REJECTION:", str(e))
            return error_response(f"Internal Database Transaction Fault: {str(e)}", 500)


# 5. SIGNUP: VERIFY OTP VIEW
class VerifySignupOTP(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        otp = serializer.validated_data["otp"]

        otp_obj = OTP.objects.filter(email=email, otp=otp, purpose="signup").first()
        if not otp_obj: return error_response("Invalid context tokens supplied.", 400)
        if otp_obj.is_expired(): return error_response("Token expiration constraint triggered.", 400)

        otp_obj.verified = True
        otp_obj.save()
        return success_response("Profile verification token verified completely.")


# 6. SIGNUP: COMPLETE FLOW (Public becomes Default Admin/Manager)
class CompleteSignup(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        data = request.data.copy()
        email = data.get("email")
        if not email: return error_response("Email pipeline context validation missing.", 400)

        if not data.get("username"):
            base_username = email.split('@')[0]
            username = base_username
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{random.randint(10, 99)}"
            data["username"] = username

        serializer = CompleteSignupSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        email_clean = serializer.validated_data.get("email")
        otp_obj = OTP.objects.filter(email=email_clean, verified=True, purpose="signup").first()
        if not otp_obj: return error_response("Unverified access path detected.", 400)

        try:
            user = CustomUser.objects.create_user(
                username=data["username"], email=email_clean,
                phone_number=serializer.validated_data.get("phone_number"),
                password=serializer.validated_data["password"],
                role='admin', # Strictly mapped to Admin tier profile roles template
                is_verified=True, is_password_set=True
            )
            UserProfile.objects.create(user=user) # Setup clean profile metadata space
            RecoveryContact.objects.create(user=user, contact_type="email", contact_value=user.email, is_verified=True)
            otp_obj.delete()

            refresh = RefreshToken.for_user(user)
            return success_response("Admin signup processed successfully.", data={"access": str(refresh.access_token), "refresh": str(refresh)}, status_code=201)
        except IntegrityError:
            return error_response("Database cluster index transaction conflict.", 400)


# 7. LOGIN VIEW
class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        login_input = request.data.get("login")
        password_input = request.data.get("password")
        if not login_input or not password_input: return error_response("Required credentials missing.", 400)

        user = authenticate(request, username=login_input, password=password_input)
        if not user: return error_response("Invalid runtime authentication mapping tokens.", 401)
        if not user.is_active: return error_response("Profile account is marked disabled.", 403)

        refresh = RefreshToken.for_user(user)
        return success_response("Token matrix authentication successful.", data={"access": str(refresh.access_token), "refresh": str(refresh)})


# 8. UPDATE FCM PUSH TOKEN VIEW
class UpdateFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        token = request.data.get('fcm_token')
        if not token: return error_response("Required data token missing from body context.", 400)
        user = request.user
        user.fcm_token = token
        user.save()
        return success_response("FCM Device Push token registered safely.", data={"user_id": str(user.id)})


# 9. USER DASHBOARD VIEW
class UserDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            user = request.user
            role = user.role
            base_data = {
                "user": {
                    "user_id": str(user.id), "username": user.username, "email": user.email,
                    "phone": user.phone_number, "name": user.name or user.username, "role": role
                }
            }
            if role == 'superuser':
                base_data["dashboard_type"] = "SUPERUSER_CORE_WORKSPACE"
                base_data["stats"] = {"total_onboarded_admins": CustomUser.objects.filter(role='admin').count()}
            elif role == 'admin':
                base_data["dashboard_type"] = "ADMIN_OPERATIONAL_WORKSPACE"
                base_data["stats"] = {"sub_admins_managed": CustomUser.objects.filter(created_by=user, role='admin').count()}

            return Response({"success": True, "data": base_data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 10. LIST STAFF VIEW (Admins / Operational Staff System Directories)
class ListStaffView(APIView):
    permission_classes = [IsAdminOrSuperuser]
    def get(self, request):
        # Superuser sees all Admins, Admin sees sub-admins registered under them
        if request.user.role == 'superuser':
            staff = CustomUser.objects.filter(role='admin')
        else:
            staff = CustomUser.objects.filter(created_by=request.user, role='admin')

        data = [
            {
                "user_id": str(user.id), "username": user.username, "email": user.email, "name": user.name,
                "is_active": user.is_active, "role": user.role,
                "profile_image": request.build_absolute_uri(user.profile.profile_image.url) if hasattr(user, 'profile') and user.profile.profile_image else None,
            }
            for user in staff
        ]
        return success_response("Operational personnel network directory synchronized.", data=data)


# 11. UNIFIED USER DIRECTORY PROFILE VIEW
class ListUsersProfileView(APIView):
    permission_classes = [IsAdminOrSuperuser]
    def get(self, request):
        role_filter = request.query_params.get('role', None)
        search_query = request.query_params.get('search', None)

        if request.user.role == 'superuser':
            queryset = CustomUser.objects.exclude(role='superuser')
        else:
            queryset = CustomUser.objects.filter(created_by=request.user, role='admin')

        if role_filter and role_filter != 'All Roles':
            queryset = queryset.filter(role=role_filter.lower())
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(email__icontains=search_query) | Q(username__icontains=search_query))

        data = []
        for user in queryset:
            profile_payload = {
                "user_id": str(user.id), "username": user.username, "email": user.email or "N/A",
                "phone": user.phone_number or "N/A", "name": user.name or user.username,
                "is_active": user.is_active, "role": user.role,
                "created_at": user.date_joined.strftime('%Y-%m-%d') if hasattr(user, 'date_joined') else None,
            }
            
            # Fetch relational UserProfile table specs fields safely
            if hasattr(user, 'profile'):
                profile_payload["profile_image"] = request.build_absolute_uri(user.profile.profile_image.url) if user.profile.profile_image else None
                profile_payload["meta_specs"] = {
                    "age": user.profile.age or "N/A",
                    "gender": user.profile.gender or "N/A",
                    "experience_years": user.profile.experience_years,
                    "hourly_rate": float(user.profile.base_rate_per_hour)
                }
            else:
                profile_payload["profile_image"] = None
                profile_payload["meta_specs"] = None

            data.append(profile_payload)

        return success_response("Unified ecosystem matrix array profiles context mapped completely.", data=data)