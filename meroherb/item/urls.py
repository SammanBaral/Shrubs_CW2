from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from .views import GeneratePDF

app_name = 'item'
urlpatterns =[
    path('new/', views.new, name='new'),
    path('browse/',views.browse,name='browse'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/delete/', views.delete, name='delete'),
    path('<int:pk>/edit/', views.edit, name='edit'),
    path('category/<str:pro>',views.Category_view,name="category_view"),
    path('buy_item/<int:pk>/', views.buy_item, name='buy_item'),
    path('generate_pdf/<int:bill_no>/', GeneratePDF.as_view(), name='generate_pdf'),
]+ static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)