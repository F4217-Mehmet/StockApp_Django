1- Öncelikle standart kurulum işlemlerimizi yapıyoruz.
2- account app ile auth işlemlerini yapıyorum. user işlemleri. dj_rest_auth paketi login logout yapmamıza imkan sağlıyor. yine aynı yerde register işlemleri yapmamı sağlayan register paketi var.
3- token authentication kullanıyorum ve tokenlerimi signal vasıtasıyla userlarıma create ediyorum.
4- Stock isminde app oluşturup, main settingsde installed apps'e ekliyorum
 # my_apps
    'account',
    'stock',

5- ERD diyagramına göre db'yi şekillendirmeye başlıyorum. Önce stock app'te models içinde modellerimi oluşturuyorum. Category'den başladım.

**********MODELS***********

from django.db import models
from django.contrib.auth.models import User

**Eğer birden fazla classta aynı metot varsa, onları ayrı bir classa çekip classlarımızı oluşturabiliriz. Buna abstract class denir. Tek amacı budur. Instance falan üretilmez.**

class UpdateCreate(models.Model): 
    createds = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

**abstract class olduğunu burada belirtiyoruz**    
    class Meta:
        abstract = True 


class Category(models.Model):
    name = models.CharField(max_length=25)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories" 
**db'de çoğulunun bu şekilde görünmesi için verbose kullanıyorum**

class Brand(models.Model):
    name = models.CharField(max_length=25, unique=True)
    image = models.TextField() **image url'ini gireceğim için textfield yazdım**
    
    def __str__(self):
        return self.name

**abstract classından**
class Product(UpdateCreate): 
    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products") 
**burada bir ürünün bir kategoride olacağı varsayımıyla onetoMany yani foreignkey kullandım ama normalde manytomany olur. Ayrıca o kategorideki productlara ulaşmak için related name verdim**
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="b_products") 
**bazen hata verdiği için burada productsa farklı related name (b_products) verdim**
    stock = models.PositiveSmallIntegerField(blank=True, default=0)
**blank=True demek, frontendden gelirken böyle bir data gelmezse sıkıntı çıkarma, serializerın validasyonunda geçiyor. ama db'den geçemez, çünkü null=True değil. o yüzden db'ye kaydetmeden önce bu fieldı eklemem gerekiyor**

    
    def __str__(self):
        return self.name

**abstract classından**
class Firm(UpdateCreate): 
    name = models.CharField(max_length=25, unique=True)
    phone = models.CharField(max_length=25)
    address = models.CharField(max_length=200)
    image = models.TextField()


    def __str__(self):
        return self.name

**abstract classından**
class Purchases(UpdateCreate): 
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True) **user silinse de işlemleri dursun**
    firm = models.ForeignKey(Firm, on_delete=models.SET_NULL, null=True, related_name="purchases")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, related_name="b_purchases")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="purchase")
    quantity = models.PositiveSmallIntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    price_total = models.DecimalField(max_digits=8, decimal_places=2, blank=True)
**blank=True demek, frontendden gelirken böyle bir data gelmezse sıkıntı çıkarma, serializerın validasyonunda geçiyor. ama db'den geçemez, çünkü null=True değil. o yüzden db'ye kaydetmeden önce bu fieldı eklemem gerekiyor**

    
    def __str__(self):
        return f'{self.product} - {self.quantity}'

**abstract classından**
class Sales(UpdateCreate): 
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, related_name="b_sales")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sale")
    quantity = models.PositiveSmallIntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    price_total = models.DecimalField(max_digits=8, decimal_places=2, blank=True)
**blank=True demek, frontendden gelirken böyle bir data gelmezse sıkıntı çıkarma, serializerın validasyonunda geçiyor. ama db'den geçemez, çünkü null=True değil. o yüzden db'ye kaydetmeden önce bu fieldı eklemem gerekiyor**

    
    def __str__(self):
        return f'{self.product} - {self.quantity}'

6- oluşturduğum modelleri **admin.py'da register** ediyorum

from django.contrib import admin
from .models import Category, Brand, Product, Firm, Purchases, Sales


admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(Firm)
admin.site.register(Purchases)
admin.site.register(Sales)


7- DB'de modellerimi ayağa kaldırmak için komutlarımı terminale yazıyorum:
python manage.py makemigrations
python manage.py migrate

8- **superuser** oluşturuyorum ve admine panele giriş yapıyorum
python manage.py createsuperuser

9- **SERIALIZER**
 şimdi stock içinde yeni file açıp serializerı yazmaya başlıyorum

from rest_framework import serializers
from .models import Category, Brand, Product, Firm, Purchases, Sales
import datetime

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()  # read_only
**kategorideki product sayısını ekledim. Serializermethodfield kullanıyorum, aşağıda metodu yazıyorum**
    
    class Meta:
        model = Category
        fields = ("id", "name", "product_count") 
**all yerine açıkça yazmak daha kullanışlı**
        
    def get_product_count(self, obj):  
**obj dediğim her bir kategori, bunlar sırayla gelip bu serializerdan geçiyorlar**
        return Product.objects.filter(category_id=obj.id).count()
**her bir kategorideki product sayısını dönüyor. bunu nasıl yapıyor? Categoryserializer Her bir kategoriyi bu serializerdan geçirirken kategoriyi argüman olarak alacak(obj) ve product tablosundaki category id'si bu kategorinin id'siyle eşit olanların sayısını dönecek.**

10- bu yazdığım serializerı **views.py'da** kullanacağım

from django.shortcuts import render
from rest_framework import viewsets, filters **filters ile search özelliği ekledim**
from .models import Category, Brand, Product, Firm, Purchases, Sales
from .serializers import CategorySerializer, CategoryProductSerializer
from rest_framework.permissions import DjangoModelPermissions

class CategoryView(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter] **search**
    search_fields = ['name'] **search**
    permission_classes=[DjangoModelPermissions]

    def get_serializer_class(self):
        if self.request.query_params.get("name"):
            return CategoryProductSerializer
        return super().get_serializer_class()

11. **viewi çalıştıracak endpoint**
öncelikle main içerisindeki viewde stock için url oluşturuyorum
urlpatterns = [
    ...
    ...
    path("stock/", include("stock.urls")),

12. şimdi de **stock içerisinde urls.py** oluşturuyorum
from django.urls import path
from rest_framework import routers
from .views import CategoryView

router = routers.DefaultRouter()

router.register("categories", CategoryView)

urlpatterns = [
    
] + router.urls  **router'a register ettiğim endpointleri bu şekilde urlpatternse ekliyorum**

13. Endpointe **filtreleme** ekliyorum. bunun için de dokümanda restframework, API guide içinde DjangoFilterBackend'den yararlanıyorum.

pip install django-filter

main settings'de installed apps'e ekliyorum.
INSTALLED_APPS = [
    ...
    # drf
    ...
    'django_filters',
]

sonra view'e gelip import yapıp Categoryview'e ekliyorum

from django_filters.rest_framework import DjangoFilterBackend

class CategoryView(viewsets.ModelViewSet):
    ...
    filter_backends = [..., DjangoFilterBackend] **filter**
    filterset_fields = ["name"] **neye göre filter yapacak**

**DJANGO FILTER GENEL BİLGİ NOTU**
yazılan kelimenin aynısını arar, mesela name için data içinde cooper varsa coop yazınca bulmaz.

A- Eğer Djangonun default FILTER ayarlarını kullanacaksak, iki farklı şekilde yapılabilir,
        #! 1 - settings içine ekleyerek;
                  INSTALLED_APPS = [ 'django_filters', ] # içine ekle
                  # en sonuna uygun bir yere DEFAULT_FILTER_BACKENDS ekle,
                  # eğer önceden REST_FRAMEWORK = { } varsa onun içine ekle, yoksa üstteki çalışmaz.
                  #? böyle yapınca global alanda tanımlanmış olur ve onu kullanır,

                  REST_FRAMEWORK = {
                      'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
                  }
                  
                  # view'da filterset_fields ekleyip, filitrelenecek alanları yazıyoruz,
                  filterset_fields = ["id", "first_name", "last_name"]

        #! 2 - views içinde import ederek
                  # settings içine birşey yazmaya gerek yok,
                  # fakat yazılsa bile local alanda olan globalı ezeceğinden import edilen çalışacaktır.
                  
                  from django_filters.rest_framework import DjangoFilterBackend

                  # view'da filter_backends ve filterset_fields ekleyip, filitrelenecek alanları yazıyoruz,
                  filter_backends = [DjangoFilterBackend]                 #? hangi filtrelemeyi kullanacak,
                  filterset_fields = ["id", "first_name", "last_name"]    #? nerede filtrelemeyi kullanacak,
                  # (hangisini kullanacaksan adını yaz)

#todo, B- Djangonun default ayarları dışında customize bir FILTER kullanmak için, filter.py ekle;
#? böyle yapınca localde çalışır ve global olanı ezer, yani settings içinde yazılsa bile burada yazılan çalışır,
daha sonra paginationda yapıldığı gibi default filter ayarları miras alınarak custom bir filter yazılabilir ve view'da import edilip kullanılabilir.

**BİLGİ NOTU SONU**

14. Şimdi de tek bir kategori çektiğimde, o kategorideki productları da görmek istiyorum. İleride ekstra özellik katacağım product classını **serializerda** oluşturmaya başlıyorum.

class ProductSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Product
        fields = "__all__"


**categoryproduct**
class CategoryProductSerializer(serializers.ModelSerializer):
    
    products = ProductSerializer(many=True) 
**products= modeldeki related name'i kullanmak zorundayım. Buradaki products, productserializerdan geçerek buraya yazılacak** **bir kategoride birden çok product olacağı için many=true**
    product_count = serializers.SerializerMethodField()  # read_only
    
    class Meta:
        model = Category
        fields = ("id", "name", "product_count", "products")
        
    def get_product_count(self, obj):
        return Product.objects.filter(category_id=obj.id).count()

15. yeni oluşturduğum serializerı view'e ekliyorum

from .serializers import ..., CategoryProductSerializer,

class CategoryView(viewsets.ModelViewSet):
        ...
        ...

    def get_serializer_class(self):
**category name'i varsa CategoryProductSerializer'ı dön diyeceğim**
        if self.request.query_params.get("name"): 
            return CategoryProductSerializer
**eğer name yoksa super().get_serializer_class()'ı çalıştır**
        return super().get_serializer_class()

16. **permission** düzenliyorum. **Djangonun user bazında ve grup olarak permission belirleme özelliğinden yararlanacağım. Adminde bunları yapabilmek için, projenin bunu algılaması için aşağıdaki işlemleri yapıyorum.**

from rest_framework.permissions import DjangoModelPermissions

**sonrasında ihtiyaç olan viewlerin altına bunu ekliyorum. Örn;**

class CategoryView(viewsets.ModelViewSet):
    ...
    ...
    permission_classes=[DjangoModelPermissions]

17. account klasöründe signals file içinde **read_only** ayarı yapıyorum ve admin panele gidip read_only grubu oluşturarak sadece view yetkisi verdim. Normal user olarak register olanlar otomatikman read_only yetkisine sahip olacak. Her bir kişi için yada gruplar halinde admin panelde yukarıdaki işlemlerim sonucunda yetki tanımlamaları yapabilirim.

receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)  
        user= User.objects.get(username = instance)
        if not user.is_superuser:
            group = Group.objects.get(name='Read_Only') 
            user.groups.add(group)
            user.save()

18. **Herhangi bir kişiyi bir gruba eklediğimde admin panelde grup isminin de görünmesi için** account  içinde admin.py'da;

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from django.contrib.auth.models import User


class UserAdminWithGroup(UserAdmin):
    def group_name(self, obj):
        queryset = obj.groups.values_list('name', flat=True)
        groups = []
        for group in queryset:
            groups.append(group)

        return ' '.join(groups)

    list_display = UserAdmin.list_display + ('group_name',)


admin.site.unregister(User)
admin.site.register(User, UserAdminWithGroup)

19. **Brand Serializer'ı** oluşturuyorum. Sırasıyla **view** ve **url** yapacağım.

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = (
            'id',
            'name',
            'image'
        )

**view**
from .models import ..., Brand
from .serializers import ..., ..., BrandSerializer

class BrandView(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

**endpoint**
from .views import ..., BrandView

router = routers.DefaultRouter()

...
router.register("brands", BrandView)

20. **Firm Serializer'ı** oluşturuyorum. Sırasıyla **view** ve **url** yapacağım.

class FirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Firm
        fields = (
            'id',
            'name',
            'phone',
            'image',
            'address'
        )

**view**
from .models import ..., ..., ..., Firm
from .serializers import ..., ..., FirmSerializer
class FirmView(viewsets.ModelViewSet):
    queryset = Firm.objects.all()
    serializer_class = FirmSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

**endpoint**
from .views import ..., ..., FirmView

router = routers.DefaultRouter()

...
router.register("firms", FirmView)


21. **Product classına yeni özellikler** ekliyorum

class ProductSerializer(serializers.ModelSerializer):

 **db'de id'lerin yanı sıra isimler de gelsin istiyorum**   
    category = serializers.StringRelatedField() **burası aslında modelsdaki category tablosundaki str!!!**
    brand = serializers.StringRelatedField()
    <!-- brand_id = serializers.IntegerField()
    category_id = serializers.IntegerField() -->

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "category",
            "category_id",
            "brand",
            "brand_id",
            "stock",
        )
**stock field sales ve purchase ile değişeceğinden read only olacak**
        read_only_fields = ("stock",) 

**view**
from .serializers import ..., ..., ProductSerializer
from .models import ..., ..., Product

class ProductView(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'brand']
    search_fields = ['name']

**endpointi**
from .views import ..., ..., ..., ProductView,

router = routers.DefaultRouter()

router.register("products", ProductView)

22. şimdi **purchase** classını oluşturuyorum

class PurchasesSerializer(serializers.ModelSerializer):
    
    user = serializers.StringRelatedField() 
    firm = serializers.StringRelatedField()
    brand = serializers.StringRelatedField()
    product = serializers.StringRelatedField()
    product_id = serializers.IntegerField()
    brand_id = serializers.IntegerField()
    firm_id = serializers.IntegerField()
    category = serializers.SerializerMethodField()
    time_hour = serializers.SerializerMethodField()
    createds = serializers.SerializerMethodField()
    
    class Meta:
        model = Purchases
        fields = (
            "id",
            "user",
            "user_id",
            "category",
            "firm",
            "firm_id",
            "brand",
            "brand_id",
            "product",
            "product_id",
            "quantity",
            "price",
            "price_total", 
**price_total'ı burada, view içerisinde yapabilirim ama signal kullanarak yapacağım**
            "time_hour",
            "createds",
        )
**purchase içerisinde kategorinin de gelmesini istiyorum. Bunu da SerizalizerMethodField ile yapıyorum**
  # def get_category(self, obj):
    #     product = Product.objects.get(id=obj.product_id)
    #     return Category.objects.get(id=product.category_id).name

**bu daha clean bir yöntem**    
    def get_category(self, obj):  
        return obj.product.category.name

 **datetime'ı import et, time_hour'u field'a ekle**

    def get_time_hour(self, obj):
        return datetime.datetime.strftime(obj.createds, "%H:%M")

 **3 aşama: 1-field'ı belirle, 2. methodu yaz 3. fieldlara ekle**      
    def get_createds(self, obj):
        return datetime.datetime.strftime(obj.createds, "%d,%m,%Y")

**böylelikle purchase'im gün ay yıl ve saat olarak kullanıcı dostu bir data olarak dönmüş oluyor**

**view**
from .models import ..., ..., ..., ..., Purchases, Sales
from .serializers import ..., .., ..., ..., ..., PurchasesSerializer
from rest_framework.response import Response

class PurchaseView(viewsets.ModelViewSet):
    queryset = Purchases.objects.all()
    serializer_class = PurchasesSerializer
    permission_classes = [DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['firm', 'product']
    search_fields = ['firm']    
    
**modelviewsetten createmodelmixin'e geldim, buradaki create metodunu alıyorum. purchase create edilirken, ilgili productın stoğunu da güncelleyeceğim** 
**Sales ve Response'u da import ediyorum**
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        #! #############  ADD Product Stock ############

**gelen datayı purchase değişkenine atadım, ilgili productı tablodan çektim ve productın stok miktarını quantity kadar artırıyorum**
        purchase = request.data 
        product = Product.objects.get(id=purchase["product_id"]) 
        product.stock += purchase["quantity"] 
        product.save()
        
        #! #############################################
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user) **purchase'i kimin yaptığını burada belirtiyorum**   
    
**Purchase'i update etme özelliğini ekliyorum. updatemodelmixin'deki update kısmını aldım.**
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object() **mevcut instance'ı alıyorum**
        serializer = self.get_serializer(instance, data=request.data, partial=partial) **serializer'da instance ile gelen datayı karşılaştırıyorum**
        serializer.is_valid(raise_exception=True) **gelen data validse mevcut instance'a gelen datayı kaydediyor**
        
        #! #############  UPDATE Product Stock ############
**purchase ve productı çekiyorum**
        purchase = request.data **yeni gelen data**
        product = Product.objects.get(id=instance.product_id)
 **şimdi logici kuruyorum**       
        sonuc = purchase["quantity"] - instance.quantity **purchase data ve instance obje olduğundan farklı yöntemlerle ulaştım**
        product.stock += sonuc
        product.save()
        #! #############################################
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

**purchase'i delete edeceğim şimdi, destroymodelmixin'den alıyorum. Mevcut instance'ın quantity'si kadarını stoktan düşüyorum.**
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        product = Product.objects.get(id=instance.product_id)
        product.stock -= instance.quantity
        product.save()
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

**endpoint**
from .views import ..., ..., ..., ..., PurchaseView

router = routers.DefaultRouter()

router.register("purchases", PurchaseView) 

22. **SIGNALS**
**price total'i hesaplamak için** stock içerisinde yeni bir signals file açıyorum. 

from django.db.models.signals import pre_save 
**!!!pre_save=purchase tablosunda purchase objesini db'ye save etmeden önce price_total'i hesaplayıp purchase objesine ekleyip db'de o şekilde save edeceğim. Çünkü price_total, blank=True olduğundan db'ye kaydetmeden önce bunu eklemem lazım.!!!**
from django.dispatch import receiver
from .models import Purchases, Sales


@receiver(pre_save, sender=Purchases) **signal'i gönderen purchases tablom**
def calculate_total_price(sender, instance, **kwargs):
    instance.price_total = instance.quantity * instance.price
    
@receiver(pre_save, sender=Sales)
def calculate_total_price(sender, instance, **kwargs):
    instance.price_total = instance.quantity * instance.price

**signal kullandığım için apps.py içerisinde aşağıdaki metodu yazdım**
    def ready(self):
        import stock.signals

