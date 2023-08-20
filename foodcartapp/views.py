from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http import JsonResponse
from django.templatetags.static import static

from phonenumber_field.validators import validate_international_phonenumber

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
        return Response({'error': 'products should be presented as a list'}, status=status.HTTP_406_NOT_ACCEPTABLE)
    elif len(products_from_response) == 0:
        return Response({'error': 'products list can not be empty'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        firstname, lastname = response['firstname'], response['lastname']
    except KeyError as e:
        return Response({'error': f'{e} is a required field'}, status=status.HTTP_400_BAD_REQUEST)
    if firstname is None:
        return Response({'error': 'firstname can not be empty'}, status=status.HTTP_400_BAD_REQUEST)
    elif lastname is None:
        return Response({'error': 'lastname can not be empty'}, status=status.HTTP_400_BAD_REQUEST)
    elif not isinstance(firstname, str):
        return Response({'error': 'firstname should be str'}, status=status.HTTP_406_NOT_ACCEPTABLE)
    elif not isinstance(lastname, str):
        return Response({'error': 'lastname should be str'}, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        phonenumber, address = response['phonenumber'], response['address']
        validate_international_phonenumber(phonenumber)
    except KeyError as e:
        return Response({'error': f'{e} is a required field'}, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError:
        return Response({'error': 'phonenumber is not correct, please make sure that you wrote correct number'},
                        status=status.HTTP_406_NOT_ACCEPTABLE)
    if phonenumber is None or len(phonenumber) < 1:
        return Response({'error': 'phonenumber can not be empty'}, status=status.HTTP_400_BAD_REQUEST)
    elif address is None:
        return Response({'error': 'address can not be empty'}, status=status.HTTP_400_BAD_REQUEST)

    products = []
    for product in products_from_response:
        try:
            products.append(Product.objects.get(pk=product['product']))
        except ObjectDoesNotExist:
            return Response({'error': 'product id does not exist'}, status=status.HTTP_400_BAD_REQUEST)
    order = Order.objects.create(
        first_name=firstname,
        last_name=lastname,
        phone_number=phonenumber,
        address=address,
    )
    order.products.set(products)
    return Response(response)
