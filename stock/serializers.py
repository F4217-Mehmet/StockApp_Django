from rest_framework import serializers
from .models import Category, Brand, Product, Firm, Purchases, Sales

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()  # read_only
    
    class Meta:
        model = Category
        fields = ("id", "name", "product_count")
        
    def get_product_count(self, obj):
        return Product.objects.filter(category_id=obj.id).count()