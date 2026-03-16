from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeaveRequestViewSet, LeaveTypeViewSet, PublicHolidayViewSet, ApprovalViewSet

router = DefaultRouter()
router.register(r'leave-requests', LeaveRequestViewSet, basename='leaverequest')
router.register(r'leave-types', LeaveTypeViewSet, basename='leavetype')
router.register(r'public-holidays', PublicHolidayViewSet, basename='publicholiday')
router.register(r'approvals', ApprovalViewSet, basename='approval')

urlpatterns = [
    path('', include(router.urls)),
]
