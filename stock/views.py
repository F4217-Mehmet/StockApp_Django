from django.shortcuts import render
from rest_framework import viewsets
from .models import Category, Brand, Product, Firm, Purchases, Sales
from .serializers import CategorySerializer

class CategoryView(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
