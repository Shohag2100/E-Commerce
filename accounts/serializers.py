from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'city', 'postal_code', 'country', 'avatar']

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['id']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
class UpdateProfileSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='profile.phone', allow_blank=True)
    address = serializers.CharField(source='profile.address', allow_blank=True)
    city = serializers.CharField(source='profile.city', allow_blank=True)
    postal_code = serializers.CharField(source='profile.postal_code', allow_blank=True)
    country = serializers.CharField(source='profile.country', allow_blank=True)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'city', 'postal_code', 'country']
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        
        # Update User fields
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        
        # Update Profile fields
        profile = instance.profile
        profile.phone = profile_data.get('phone', profile.phone)
        profile.address = profile_data.get('address', profile.address)
        profile.city = profile_data.get('city', profile.city)
        profile.postal_code = profile_data.get('postal_code', profile.postal_code)
        profile.country = profile_data.get('country', profile.country)
        profile.save()
        
        return instance