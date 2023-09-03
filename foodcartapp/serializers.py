from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.fields import CharField
from rest_framework.serializers import Serializer, ModelSerializer

from foodcartapp.models import Order


class OrderSerializer(ModelSerializer):
    firstname = CharField(max_length=200)
    lastname = CharField(max_length=200)
    phonenumber = PhoneNumberField(region='RU')

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']
