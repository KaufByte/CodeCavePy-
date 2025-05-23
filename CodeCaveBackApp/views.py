# CodeCaveBackApp/views.py

from decimal import Decimal
from operator import inv
import random
import string
from django.http import Http404
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.generics import DestroyAPIView
from django.core.mail import EmailMessage
import requests
from .models import CustomUser, Video,Comment
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    EmailTokenSerializer,
    SupportSerializer,
    CommentSerializer
)
from django.conf import settings
from .serializers import VideoSerializer
from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.conf import settings
import stripe 
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from django.utils.decorators import method_decorator
stripe.api_key = settings.STRIPE_SECRET_KEY 

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        if ser.is_valid():
            user = ser.save()
            token_ser = EmailTokenSerializer(data={
                'email':    request.data['email'],
                'password': request.data['password'],
            })
            token_ser.is_valid(raise_exception=True)
            return Response(token_ser.validated_data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

class EmailTokenObtainView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        ser = EmailTokenSerializer(data=request.data)
        if ser.is_valid():
            return Response(ser.validated_data, status=status.HTTP_200_OK)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

class ListUsersView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/users/<id>/   — проглянути
    PATCH  /api/users/<id>/   — оновити
    DELETE /api/users/<id>/   — видалити
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated] 
    lookup_field = 'id'
    
class GetUserByEmail(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        email = self.request.query_params.get("email")
        if not email:
            raise Http404("Email is required")
        try:
            return CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise Http404("Пользователь не найден")

def get_location(request):
    res = requests.get("http://ip-api.com/json/")
    return JsonResponse(res.json())

class UserDeleteView(DestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

class SupportView(APIView):
    def post(self, request):
        serializer = SupportSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            message = serializer.validated_data['message']

            subject = "🛠 Support Request from User"
            body = f"📧 Email: {email}\n\n📝 Message:\n{message}"

            try:
                mail = EmailMessage(
                    subject,
                    body,
                    from_email=settings.DEFAULT_FROM_EMAIL, 
                    to=["dmitrijfriday3@gmail.com"]
                )
                mail.send()
                return Response({"success": "Message sent successfully!"}, status=200)
            except Exception as e:
                print("Error sending email:", e)
                return Response({"error": "Failed to send email"}, status=500)

        return Response(serializer.errors, status=400)
class VideoListCreateView(generics.ListCreateAPIView):
    queryset = Video.objects.all().order_by("-id")
    serializer_class = VideoSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_context(self):
        return {"request": self.request}
class VideoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_context(self):
        return {"request": self.request}

class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Comment.objects.all().order_by('date')
        video_id = self.request.query_params.get('video')
        if video_id is not None:
            qs = qs.filter(video_id=video_id)
        return qs

    def perform_create(self, serializer):
        user = CustomUser.objects.get(email=self.request.data.get("user_email"))
        video = Video.objects.get(id=self.request.data.get("video"))
        parent = Comment.objects.filter(id=self.request.data.get("parent")).first()
        serializer.save(user=user, video=video, parent=parent)

class CommentUpdateView(generics.UpdateAPIView):
    queryset = Comment.objects.all()  
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
class CommentDeleteView(generics.DestroyAPIView):
    queryset = Comment.objects.all()  
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
class CommentCountView(APIView):
    def get(self, request):
        from collections import Counter
        counts = Counter(Comment.objects.values_list('video_id', flat=True))
        return Response(dict(counts))

class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=400)

        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        
        user.password = make_password(new_password)
        user.save()

        
        try:
            send_mail(
                subject="🔐 Password Reset | CodeCave",
                message=f"Hello {user.username},\n\nYour new password is: {new_password}\n\nYou can change it in your account settings after login.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return Response({"success": "New password sent to your email"}, status=200)
        except Exception as e:
            print("Email sending failed:", e)
            return Response({"error": "Failed to send email"}, status=500)

class CreateSetupIntnet(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(email=user.email)
            user.stripe_customer_id = customer.id
            user.save()
        else:
            customer = stripe.Customer.retrieve(user.stripe_customer_id)

        setup_intent = stripe.SetupIntent.create(customer=customer.id,usage="off_session")

        return Response({
            "clientSecret": setup_intent.client_secret,
            "customerId": customer.id
        })


class CreateCheckoutSession(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        price_id = request.data.get("priceId")

        print("POST /checkout-session")
        print("User:", user)
        print("User email:", user.email)
        print("Price ID:", price_id)

        if not price_id:
            return Response({"error": "Missing priceId"}, status=400)

        if not user.email:
            return Response({"error": "User has no email"}, status=400)

        try:
            if not user.stripe_customer_id:
                print("Creating Stripe customer...")
                customer = stripe.Customer.create(email=user.email)
                user.stripe_customer_id = customer.id
                user.save()
                print("Customer created:", customer.id)

            print("Creating Stripe checkout session...")
            # session = stripe.checkout.Session.create(
            #     customer=user.stripe_customer_id,
            #     mode="subscription",  
            #     line_items=[{"price": price_id, "quantity": 1}],
            #     success_url="https://codecave.vercel.app/success",
            #     cancel_url="https://codecave.vercel.app/cancel",
            #     payment_method_types=["card"],
            #     allow_promotion_codes=True,  
            #     subscription_data={
            #         "metadata": {"user_id": str(user.id)}
            #     }
            # )
            session = stripe.checkout.Session.create(
                customer=user.stripe_customer_id,
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                success_url="https://codecave.vercel.app/success",
                cancel_url="https://codecave.vercel.app/cancel",
                payment_method_types=["card"],
                allow_promotion_codes=True,
                expand=["subscription"],
            )
            print("✅ Session created:", session.id)
            return Response({"sessionId": session.id})

        except Exception as e:
            import traceback
            traceback.print_exc()
            print("❌ Stripe error:", str(e))
            return Response({"error": str(e)}, status=500)




class GetPaymentMethod(APIView):
    permission_classes =[IsAuthenticated]

    def get(self,request):
        user = request.user
        if not user.stripe_customer_id:
            return Response([])
        try:
            methods = stripe.PaymentMethod.list(
                customer=user.stripe_customer_id,
                type="card"
            )
            return Response(methods.data)
        except Exception as e:
            return Response({"error": str(e)},status=500)

class Getnvoices(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        user = request.user 
        if not user.stripe_customer_id:
            return Response([])
        
        try:
            invoices = stripe.Invoice.list(customer=user.stripe_customer_id)
            result = [
                {
                    "id": inv.id,
                    "amount":inv.amount_paid/100,
                    "currency": inv.currency, 
                    "status": inv.status,
                    "date": inv.created,
                }
                for inv in invoices.auto_paging_iter()
            ]
            return Response(result)
        except Exception as e: 
            return Response({"error": str(e)},status= 500)
class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.stripe_customer_id:
            return Response({"error": "No Stripe customer"}, status=400)

        subscriptions = stripe.Subscription.list(customer=user.stripe_customer_id)
        active_sub = next((s for s in subscriptions.auto_paging_iter() if s["status"] == "active"), None)

        if not active_sub:
            return Response({"error": "No active subscription found"}, status=404)

        stripe.Subscription.delete(active_sub.id)

        user.subscription_status = "canceled"
        user.subscription_name = "price_FREE"
        user.subscription_price = "0.00"
        user.subscription_description = ""
        user.save()

        return Response({"message": "Subscription canceled"})
stripe.api_key = settings.STRIPE_SECRET_KEY
@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError:
            return Response(status=400)  
        except stripe.error.SignatureVerificationError:
            return Response(status=400)  

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            customer_id = session.get('customer')
            metadata = session.get('metadata', {})

            if metadata.get("type") == "balance_topup":
                try:
                    user_id = metadata.get("user_id")
                    amount = int(metadata.get("amount", "0"))
                    user = CustomUser.objects.get(id=user_id)
                    user.balance += Decimal(amount) / Decimal("100") 
                    user.save()
                    print(f"✅ Баланс поповнен на {amount/100} EUR для користувача {user.email}")
                except Exception as e:
                    print("❌ Ошибка при пополнении баланса:", e)

            elif customer_id and session.get("subscription"):
                try:
                    user = CustomUser.objects.get(stripe_customer_id=customer_id)
                    sub = stripe.Subscription.retrieve(session["subscription"])
                    plan = sub['items']['data'][0]['plan']
                    price_id = plan['id']

                    user.subscription_status = sub.status
                    user.subscription_name = price_id
                    user.subscription_price = f"{plan['amount'] / 100:.2f}"
                    user.subscription_description = plan.get('nickname', '') or plan.get('id')
                    user.save()
                    print(f"✅ Підписка активована для корситувача {user.email}")
                except CustomUser.DoesNotExist:
                    print("❌ Користувач с таким Stripe ID не знайден")
        return Response(status=200)

class DeletePaymentMethodView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, payment_method_id):
        user = request.user

        try:
            methods = stripe.PaymentMethod.list(customer=user.stripe_customer_id, type="card")
            if not any(pm.id == payment_method_id for pm in methods.data):
                return Response({"error": "Payment method not found or does not belong to user"}, status=404)

            stripe.PaymentMethod.detach(payment_method_id)
            return Response({"message": "Card deleted successfully"})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
class GetStripeCustomerIdView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"customerId": request.user.stripe_customer_id})
class CreateStrictSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        price_id = request.data.get("priceId")

        if not price_id:
            return Response({"error": "Missing parameters"}, status=400)

        if not user.stripe_customer_id:
            customer = stripe.Customer.create(email=user.email)
            user.stripe_customer_id = customer.id
            user.save()

        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=user.stripe_customer_id,
                type="card"
            )
            if not payment_methods.data:
                return Response({"error": "No saved card found"}, status=400)

            default_pm = payment_methods.data[0].id

            subscription = stripe.Subscription.create(
                customer=user.stripe_customer_id,
                items=[{"price": price_id}],
                default_payment_method=default_pm,
                expand=["latest_invoice"], 
            )

            plan = subscription['items']['data'][0]['plan']
            user.subscription_status = subscription.status
            user.subscription_name = price_id
            user.subscription_price = f"{plan['amount'] / 100:.2f}"
            user.subscription_description = plan.get('nickname', '') or plan.get('id')
            user.save()

            return Response({"message": "Subscription created"})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)

class CreateTopUpSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        amount = request.data.get("amount")

        try:
            amount = int(float(amount) * 100) 
            if amount <= 0:
                return Response({"error": "Invalid amount"}, status=400)
        except:
            return Response({"error": "Invalid amount"}, status=400)

        if not user.stripe_customer_id:
            customer = stripe.Customer.create(email=user.email)
            user.stripe_customer_id = customer.id
            user.save()

        try:
            session = stripe.checkout.Session.create(
                customer=user.stripe_customer_id,
                mode="payment",
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": "Balance Top-Up",
                        },
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                }],
                success_url="http://localhost:5173/success?type=topup",
                cancel_url="http://localhost:5173/cancel",
                metadata={
                    "user_id": str(user.id),
                    "type": "balance_topup",
                    "amount": str(amount),
                },
            )
            return Response({"sessionId": session.id})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
class SubscribeUsingBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        price_id = request.data.get("priceId")
        price_map = {
            "price_1RDBbICBzupUl6DZvborkf3k": Decimal("5.00"),
            "price_1RDBhUCBzupUl6DZnaT7g5HH": Decimal("10.00"),
            "price_1RDBibCBzupUl6DZd9ojFaDE": Decimal("20.00"),
        }

        if price_id not in price_map:
            return Response({"error": "Invalid priceId"}, status=400)

        price = price_map[price_id]

        if user.balance < price:
            return Response({"error": "Insufficient balance"}, status=400)
        user.balance -= price
        user.subscription_status = "active"
        user.subscription_name = price_id
        user.subscription_price = f"{price:.2f}"
        user.subscription_description = "Purchased with balance"
        user.save()

        return Response({"success": f"Subscribed using {price:.2f} EUR balance"})
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    return Response(UserSerializer(request.user).data)

class CheckDuplicateCardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_method_id):
        user = request.user

        try:
            new_method = stripe.PaymentMethod.retrieve(payment_method_id)
            new_fp = new_method.card.fingerprint

            existing_methods = stripe.PaymentMethod.list(
                customer=user.stripe_customer_id,
                type="card"
            )

            for method in existing_methods.data:
                if method.card.fingerprint == new_fp:
                    return Response({"exists": True})

            return Response({"exists": False})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
class AdminCancelSubscriptionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if user.stripe_customer_id:
            subscriptions = stripe.Subscription.list(customer=user.stripe_customer_id)
            active_sub = next((s for s in subscriptions.auto_paging_iter() if s["status"] == "active"), None)

            if active_sub:
                try:
                    stripe.Subscription.delete(active_sub.id)
                except Exception as e:
                    return Response({"error": f"Stripe error: {str(e)}"}, status=400)

        user.subscription_status = "canceled"
        user.subscription_name = "Free"
        user.subscription_price = "0.00"
        user.subscription_description = ""
        user.save()

        return Response({"message": "Subscription canceled (locally and/or in Stripe)"})

