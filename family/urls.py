from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view),
    path('login/', views.login_view),
    path('logout/', views.logout_view),
    path('dashboard/', views.dashboard_view),
    path('members/', views.members_view),
    path('members/add/', views.add_member_view),
    path('members/edit/<int:pk>/', views.edit_member_view),
    path('members/delete/<int:pk>/', views.delete_member_view),
    path('relationships/', views.relationships_view),
    path('relationships/add/', views.add_relationship_view),
    path('relationships/delete/<int:pk>/', views.delete_relationship_view),
    path('find/', views.find_relationship_view),
    path('tree/', views.family_tree_view),
]