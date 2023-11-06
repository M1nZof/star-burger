import requests

from collections import defaultdict
from geopy import distance

from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Sum, F
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from places.models import Place
from places.utils import fetch_coordinates
from star_burger.custom_errors import YandexApiError
from star_burger.settings import YANDEX_API_KEY


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = PhoneNumberField()

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def total_price(self):
        price = Sum(F('sets__quantity') * F('sets__price'))
        return self.prefetch_related('sets').annotate(total_price=price)

    def get_available_restaurants(self):
        restaurant_and_menus = RestaurantMenuItem.objects.prefetch_related('product', 'restaurant')
        available_products_in_rests = defaultdict(list)
        for rest_product in restaurant_and_menus:
            if rest_product.availability:
                available_products_in_rests[rest_product.restaurant].append(rest_product.product)
                available_products_in_rests[rest_product.restaurant].append(rest_product.restaurant.address)

        for order in self:
            order.available_in = []
            product_set = order.sets.filter(order=order).prefetch_related('product')
            for restaurant, data in available_products_in_rests.items():
                if all(i in data[0:-1] for i in [x.product for x in product_set]):
                    try:
                        order_place = Place.objects.get(address=order.address)
                        order_lon, order_lat = order_place.longitude, order_place.latitude
                    except Place.DoesNotExist:
                        order_lon, order_lat = fetch_coordinates(YANDEX_API_KEY, order.address)
                        order_place = Place.objects.create(address=order.address, latitude=order_lat,
                                                           longitude=order_lon)
                        order_place.save()
                    except YandexApiError as e:
                        print(e)
                        order_lon, order_lat = None, None
                    try:
                        rest_place = Place.objects.get(address=restaurant.address)
                        rest_lon, rest_lat = rest_place.longitude, rest_place.latitude
                    except Place.DoesNotExist:
                        rest_lon, rest_lat = fetch_coordinates(YANDEX_API_KEY, restaurant.address)
                        rest_place = Place.objects.create(address=restaurant.address, latitude=rest_lat,
                                                          longitude=rest_lon)
                        rest_place.save()
                    except YandexApiError as e:
                        print(e)
                        rest_lon, rest_lat = None, None
                    order.distance_from_rest_to_recipient = distance.distance((rest_lat, rest_lon),
                                                                              (order_lat, order_lon)).km
                    order.available_in.append(restaurant.name)
            if not order.available_in:
                order.available_in = ['Ни один ресторан не может выполнить заказ!']
        return list(self)


class Order(models.Model):
    STATUSES = [
        ('Unprocessed', 'Необработанный'),
        ('Assembling', 'Cборка'),
        ('Delivery', 'Доставка'),
        ('Completed', 'Выполнен'),
    ]
    PAYMENT_METHODS = [
        ('Card', 'Картой на сайте'),
        ('Cash', 'Наличными'),
    ]

    firstname = models.CharField(max_length=200, verbose_name='Имя')
    lastname = models.CharField(max_length=200, verbose_name='Фамилия')
    phonenumber = PhoneNumberField(region='RU', verbose_name='Телефон')
    address = models.CharField(max_length=200, verbose_name='Адрес доставки')
    status = models.CharField(max_length=200, verbose_name='Статус', choices=STATUSES, db_index=True)
    comment = models.CharField(max_length=200, blank=True, null=True, verbose_name='Комментарий')
    products = models.ManyToManyField(
        Product,
        related_name='products',
        verbose_name='Товар'
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='Дата создания')
    called_at = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name='Дата звонка')
    delivered_at = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name='Дата доставки')
    payment_method = models.CharField(max_length=200, verbose_name='Способ оплаты',
                                      choices=PAYMENT_METHODS, db_index=True)
    performer = models.ForeignKey(Restaurant, on_delete=models.PROTECT, verbose_name='Ресторан', default=None,
                                  blank=True, null=True, related_name='orders')

    objects = OrderQuerySet.as_manager()

    @property
    def get_payment_method_display(self):
        for method_from_choice in self.PAYMENT_METHODS:
            if str(method_from_choice) == self.payment_method or method_from_choice[0] == self.payment_method:
                return method_from_choice[1]

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.lastname} {self.firstname} - {self.address}'


class ProductSet(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField('Количество', default=1, blank=True)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='sets')
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
