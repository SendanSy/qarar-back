from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import UserInterest

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that adds user data to token response
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom claims
        data.update({
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'user_type': self.user.user_type,
            'is_verified': self.user.is_verified,
        })
        
        return data


class UserInterestSerializer(serializers.ModelSerializer):
    """
    Serializer for user interests
    """
    class Meta:
        model = UserInterest
        fields = ('id', 'name')


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal user serializer with basic info (for lists, mentions, etc.)
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'profile_picture', 'is_verified', 'user_type', 'first_name', 'last_name')
        ref_name = "UserMinimalSerializerUsers"


class UserSerializer(serializers.ModelSerializer):
    """
    Standard user serializer for general use
    """
    interests = UserInterestSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'bio', 'profile_picture', 'cover_photo', 'website', 'location',
            'user_type', 'twitter', 'facebook', 'instagram', 'linkedin',
            'is_verified', 'date_joined', 'interests',
        )
        read_only_fields = ('email', 'date_joined', 'is_verified')


class UserDetailSerializer(UserSerializer):
    """
    Detailed user serializer with all fields
    """
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    User registration serializer with password validation
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    interests = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password2', 'first_name', 
            'last_name', 'bio', 'user_type', 'interests'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'password2': {'write_only': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        interests_data = validated_data.pop('interests', [])
        
        user = User.objects.create_user(**validated_data)
        
        # Create user interests
        for interest_name in interests_data:
            UserInterest.objects.create(user=user, name=interest_name)
        
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value 