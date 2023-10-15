from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Sum, F
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


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
    restaurant = models.ForeignKey(Restaurant, on_delete=models.PROTECT, verbose_name='Ресторан', default=None,
                                   blank=True, null=True)

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
