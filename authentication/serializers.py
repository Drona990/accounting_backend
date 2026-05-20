from rest_framework import serializers
from .models import CustomUser


class CheckUsernameSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)


class SignupSendOTPSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True) # 🌟 NOW OPTIONAL
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)

    def validate(self, data):
        if not data.get("email") and not data.get("phone_number"):
            raise serializers.ValidationError("Email or phone number required")
        if CustomUser.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError("Username already exists")
        return data


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        if not data.get("email") and not data.get("phone_number"):
            raise serializers.ValidationError(
                "Email or phone number is required"
            )
        return data

class CompleteSignupSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    password = serializers.CharField(min_length=6)

    name = serializers.CharField(required=False)
    dob = serializers.DateField(required=False)
    gender = serializers.CharField(required=False)


class ForgotPasswordSendOTPSerializer(serializers.Serializer):
    contact = serializers.CharField()


# ===== ROLE-BASED SERIALIZERS =====

class CreateSuperuserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=100, required=True)
    last_name = serializers.CharField(max_length=100, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    profile_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'password', 'profile_image']




class CreateAdminSerializer(serializers.Serializer):
    # Core Fields matching your Flutter payload
    first_name = serializers.CharField(max_length=100, required=True)
    last_name = serializers.CharField(max_length=100, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(min_length=8, write_only=True)
    
    # Optional parameters matching models.py keys exactly
    phone_number = serializers.CharField(required=False, allow_blank=True, default="")
    age = serializers.CharField(required=False, allow_blank=True, default="")
    gender = serializers.CharField(required=False, allow_blank=True, default="MALE")

    def validate_email(self, value):
        # Prevent dirty duplicate entry overlaps
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email profile identity is already registered.")
        return value

    def validate_phone_number(self, value):
        if value and CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number matrix is already assigned.")
        return value



class UpdateAdminProfileSerializer(serializers.Serializer):
    # Core Data properties targets mapping
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    age = serializers.CharField(required=False, allow_blank=True, default="")
    password = serializers.CharField(min_length=8, write_only=True, required=False, allow_blank=True)

    def validate_age(self, value):
        # Prevent fractional strings tokens crashes
        if value and not str(value).strip().isdigit():
            raise serializers.ValidationError("Age dynamic criteria parameters must be a clean numeric digit.")
        return value

class CreateStaffSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    name = serializers.CharField(required=False)
    role = serializers.CharField(required=False) # 👈 Ye field add karna zaruri hai

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value


class UpdateProfileSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    dob = serializers.DateField(required=False)
    gender = serializers.CharField(required=False)

class ForgotPasswordVerifyOTPSerializer(serializers.Serializer):
    contact = serializers.CharField()
    otp = serializers.CharField(max_length=6)


class ForgotPasswordResetSerializer(serializers.Serializer):
    contact = serializers.CharField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=6)
