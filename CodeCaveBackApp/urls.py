from django.urls import path, re_path

from .views import (
    AdminCancelSubscriptionView, CancelSubscriptionView, CheckDuplicateCardView, CommentCountView, CommentDeleteView, CommentListCreateView, CommentUpdateView, CreateCheckoutSession, CreateSetupIntnet,CreateStrictSubscriptionView, CreateTopUpSessionView, DeletePaymentMethodView, GetPaymentMethod, GetStripeCustomerIdView, Getnvoices,
    PasswordResetView, RegisterView, StripeWebhookView, SubscribeUsingBalanceView, UserDeleteView, UserDetailView,
    GetUserByEmail, ListUsersView, VideoListCreateView, VideoRetrieveUpdateDestroyView, get_current_user
)
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, EmailTokenObtainView, ListUsersView, UserDetailView, GetUserByEmail,get_location,SupportView
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    # получение JWT по email+паролю
    path('token/', EmailTokenObtainView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('users/<int:id>/', UserDetailView.as_view(), name='user-detail'),
    path('users/', ListUsersView.as_view()),
    path('user/', GetUserByEmail.as_view()),
    path("location/",get_location),
    path('users/<int:id>/delete/', UserDeleteView.as_view(), name='delete_user'),
    path("support/",SupportView.as_view()),
    path("videos/",VideoListCreateView.as_view()),
    path("videos/<int:pk>/",VideoRetrieveUpdateDestroyView.as_view()),
    path("comments/", CommentListCreateView.as_view(), name="comment-list-create"),
    path("comments/<int:pk>/", CommentUpdateView.as_view(), name="comment-update"),
    path("comments/<int:pk>/delete/", CommentDeleteView.as_view(), name="comment-delete"),
    path("comments-count/", CommentCountView.as_view()),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path("stripe/setup-intent/", CreateSetupIntnet.as_view()),
    path("stripe/checkout-session/", CreateCheckoutSession.as_view()),
    path("stripe/payment-methods/", GetPaymentMethod.as_view()),
    path("stripe/invoices/", Getnvoices.as_view()),
    path("stripe/cancel-subscription/", CancelSubscriptionView.as_view(), name="cancel-subscription"),
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path("stripe/payment-methods/<str:payment_method_id>/", DeletePaymentMethodView.as_view(), name="delete-payment-method"),
    path("stripe/customer-id/", GetStripeCustomerIdView.as_view(), name="stripe-customer-id"),
    path("stripe/create-strict-subscription/", CreateStrictSubscriptionView.as_view()),
    path("stripe/topup-session/", CreateTopUpSessionView.as_view()),
    path("stripe/subscribe-with-balance/", SubscribeUsingBalanceView.as_view(), name="subscribe-with-balance"),
    path("me/",get_current_user),
    path("stripe/check-duplicate/<str:payment_method_id>/", CheckDuplicateCardView.as_view()),
    path("admin/cancel-subscription/<int:user_id>/", AdminCancelSubscriptionView.as_view()),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)