from . import views
from django.urls import path


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact, name='contact'),
    path('videos/', views.videos, name='videos'),
    path('blog/', views.blog, name='blog'),
    path('blog/<slug:slug>/', views.blog_detail, name='post_detail'),
    path('sitemap.xml', views.sitemap, name='sitemap'),
]