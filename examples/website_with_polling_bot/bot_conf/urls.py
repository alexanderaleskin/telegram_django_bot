from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # path('payment/', include(('payment.urls', 'payment'), namespace='payment')),

]
