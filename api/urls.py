from django.urls import path
from .views import TotalSalesOverTime, NewCustomersOverTime, RepeatCustomers, GeographicalDistribution, CustomerLifetimeValue

urlpatterns = [
    path('total-sales/', TotalSalesOverTime.as_view(), name='total-sales'),
    path('new-customers/', NewCustomersOverTime.as_view(), name='new-customers'),
    path('repeat-customers/', RepeatCustomers.as_view(), name='repeat-customers'),
    path('geographical-distribution/', GeographicalDistribution.as_view(), name='geographical-distribution'),
    path('customer-lifetime-value/', CustomerLifetimeValue.as_view(), name='customer-lifetime-value'),
]
