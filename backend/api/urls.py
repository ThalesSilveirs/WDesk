from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TicketViewSet, ConnectionViewSet, WebhookView, UserViewSet, CustomerViewSet, 
    CustomerContactViewSet, ContactViewSet, CompanyViewSet, QuickReplyViewSet, 
    AbsenceScheduleViewSet, CityViewSet, PendencyViewSet, PendencyMovementViewSet
)

router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'connections', ConnectionViewSet, basename='connection')
router.register(r'users', UserViewSet, basename='user')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'customer-contacts', CustomerContactViewSet, basename='customer-contact')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'quick-replies', QuickReplyViewSet, basename='quick-reply')
router.register(r'absence-schedules', AbsenceScheduleViewSet, basename='absence-schedule')
router.register(r'cities', CityViewSet, basename='city')
router.register(r'pendencies', PendencyViewSet, basename='pendency')
router.register(r'pendency-movements', PendencyMovementViewSet, basename='pendency-movement')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/evolution/', WebhookView.as_view({'post': 'evolution', 'get': 'evolution'}), name='webhook_evolution'),
    path('webhooks/evolution', WebhookView.as_view({'post': 'evolution', 'get': 'evolution'})),
]
