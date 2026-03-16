from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeaveRequestViewSet, LeaveTypeViewSet, ApprovalViewSet

router = DefaultRouter()
router.register(r'requests', LeaveRequestViewSet, basename='leave-request')
router.register(r'types', LeaveTypeViewSet, basename='leave-type')
router.register(r'approvals', ApprovalViewSet, basename='approval')

urlpatterns = [
    path('', include(router.urls)),
]
