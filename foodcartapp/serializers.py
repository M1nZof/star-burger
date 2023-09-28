from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.fields import CharField, IntegerField
from rest_framework.serializers import Serializer, ModelSerializer

from foodcartapp.models import Order, ProductSet


class OrderItemSerializer(ModelSerializer):
    class Meta:
        model = ProductSet
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    firstname = CharField(max_length=200)
    lastname = CharField(max_length=200)
    phonenumber = PhoneNumberField(region='RU')
    products = OrderItemSerializer(many=True, allow_empty=False, write_only=True)

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        for product_data in products_data:
            ProductSet.objects.create(order=order, price=product_data['product'].price, **product_data)
        return order

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']
