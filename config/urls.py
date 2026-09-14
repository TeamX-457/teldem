from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("devices/", include("apps.devices.urls")),
    path("alerts/", include("apps.alerts.urls")),
    path("billing/", include("apps.billing.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("", include("apps.marketing.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "TELDEM AI Operations"
admin.site.site_title = "TELDEM AI Admin"
admin.site.index_title = "Platform administration"

handler404 = "apps.marketing.views_errors.custom_404"
handler500 = "apps.marketing.views_errors.custom_500"
