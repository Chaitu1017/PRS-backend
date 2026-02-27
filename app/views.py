from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .threads import *
from .models import *



# -------------------------
# SIGNUP
# -------------------------
@api_view(["POST"])
def signUp(request):
    try:
        serializer = signupSerializer(data=request.data)

        if serializer.is_valid():
            name = serializer.validated_data["name"]
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            if UserModel.objects.filter(email=email).exists():
                return Response(
                    {"message": "Account already exists."},
                    status=status.HTTP_406_NOT_ACCEPTABLE
                )

            user = UserModel.objects.create(email=email, name=name)
            user.set_password(password)
            user.save()

            return Response(
                {"message": "Account created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------------
# LOGIN
# -------------------------
@api_view(["POST"])
def logIn(request):
    try:
        serializer = loginSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            user = authenticate(email=email, password=password)

            if not user:
                return Response(
                    {"message": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Login successful",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh)
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

import random


@api_view(["POST"])
def forgot(request):
    try:
        serializer = ForgotSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]

            user = UserModel.objects.filter(email=email).first()

            if not user:
                return Response(
                    {"message": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            otp = random.randint(100000, 999999)
            user.otp = otp
            user.save()

            print(f"OTP for {email} is {otp}")

            return Response(
                {"message": "OTP sent successfully (check server console)"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def reset(request):
    try:
        serializer = ResetSerializer(data=request.data)

        if serializer.is_valid():
            otp = serializer.validated_data["otp"]
            new_password = serializer.validated_data["new_password"]

            user = UserModel.objects.filter(otp=otp).first()

            if not user:
                return Response(
                    {"message": "Invalid OTP"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(new_password)
            user.otp = 0
            user.save()

            return Response(
                {"message": "Password reset successful"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# -------------------------
# SAVE HEALTH DATA
# -------------------------
@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def health(request):
    try:
        serializer = healthSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user

            user.height = serializer.validated_data["height"]
            user.weight = serializer.validated_data["weight"]
            user.smoking = serializer.validated_data["smoking"]
            user.alcoholic = serializer.validated_data["alcoholic"]
            user.dob = serializer.validated_data["dob"]
            user.gender = serializer.validated_data["gender"]
            user.save()

            return Response(
                {"message": "Health data saved successfully"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------------
# SAVE MEDICAL DATA
# -------------------------
@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getData(request):
    try:
        serializer = UserDataSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            user_data, _ = UserData.objects.get_or_create(user=user)

            user_data.ecg = serializer.validated_data["ecg"]
            user_data.bps = serializer.validated_data["bps"]
            user_data.bpd = serializer.validated_data["bpd"]
            user_data.cardio = serializer.validated_data["cardio"]
            user_data.save()

            return Response(
                {"message": "Medical data saved successfully"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------------
# CHECK IF USER FILLED DATA
# -------------------------
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def checkData(request):
    try:
        user = request.user
        has_filled = bool(user.height)

        return Response(
            {"has_filled": has_filled},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------------
# START ANALYSIS (THREADS)
# -------------------------
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def analyseData(request):
    try:
        user = request.user
        user_data = UserData.objects.get(user=user)

        GlucoseDataThread(user_data).start()
        CardioDataThread(user_data).start()
        ECGDataThread(user_data).start()

        return Response(
            {"message": "Analysis started"},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------------
# FETCH RESULTS + INSURANCE RECOMMENDATION
# -------------------------
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def fetchResults(request):
    try:
        user = request.user
        user_data = UserData.objects.get(user=user)

        # Check if results are ready
        if not user_data.ecg or not user_data.glucose or user_data.cardio is None:
            return Response(
                {"message": "Results not ready. Please try again shortly."},
                status=status.HTTP_406_NOT_ACCEPTABLE
            )

        # -------------------------
        # Insurance Risk Logic
        # -------------------------
        risk_score = 0

        if user_data.glucose > 150:
            risk_score += 2

        if user_data.cardio == 1:
            risk_score += 2

        if user.smoking:
            risk_score += 1

        if risk_score >= 4:
            plan = "Premium Gold Plan"
            premium = 15000
            coverage = "20 Lakhs"
            risk_level = "High"

        elif risk_score >= 2:
            plan = "Standard Silver Plan"
            premium = 9000
            coverage = "10 Lakhs"
            risk_level = "Moderate"

        else:
            plan = "Basic Bronze Plan"
            premium = 5000
            coverage = "5 Lakhs"
            risk_level = "Low"

        return Response({
            "ecg": user_data.ecg,
            "glucose": user_data.glucose,
            "cardio": user_data.cardio,
            "recommended_plan": plan,
            "premium": premium,
            "coverage": coverage,
            "risk_level": risk_level
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)