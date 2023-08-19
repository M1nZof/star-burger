import json

from django.http import JsonResponse
from django.templatetags.static import static

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product, Order


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    response = request.data
    try:
        products_from_response = response['products']
    except KeyError:
        return Response({'error': 'products can not be empty'}, status=status.HTTP_400_BAD_REQUEST)
    if products_from_response is None:
        return Response({'error': 'products can not be null'}, status=status.HTTP_400_BAD_REQUEST)
    elif not isinstance(products_from_response, list):
        return Response({'error': 'products should be presented as a list'}, status=status.HTTP_400_BAD_REQUEST)
    elif len(products_from_response) == 0:
        return Response({'error': 'products list can not be empty'}, status=status.HTTP_400_BAD_REQUEST)
    firstname, lastname = response['firstname'], response['lastname']
    phonenumber, address = response['phonenumber'], response['address']
    products = []
    for product in products_from_response:
        products.append(Product.objects.get(pk=product['product']))
    order = Order.objects.create(
        first_name=firstname,
        last_name=lastname,
        phone_number=phonenumber,
        address=address,
    )
    order.products.set(products)
    return Response(response)
