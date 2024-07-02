from django.contrib import admin
from django.urls import path, include, re_path

from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="taxi-project",
        default_version='1.1.1',
        description="멋쟁이 사자처럼 인하대 해커톤 2팀 api 문서",
        terms_of_service="https://www.google.com/policies/terms/"
    ),
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('myAPP.urls')),

    # Swagger url
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
