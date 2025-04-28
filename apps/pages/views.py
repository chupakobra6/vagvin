from django.shortcuts import render
from django.templatetags.static import static
from django.http import HttpResponse, JsonResponse
import random
from datetime import datetime, timedelta
import json
import logging
from django.views.decorators.http import require_GET
from django.core.cache import cache
from .services import (
    check_autoteka,
    check_carfax_autocheck,
    check_vinhistory,
    check_auction,
    generate_cache_key,
    extract_avito_id,
    CACHE_TTL,
    CACHE_TIME_SHORT,
    CACHE_TIME_LONG,
    get_avito_token
)
from django.views.decorators.csrf import csrf_exempt
from json.decoder import JSONDecodeError
from django.views.decorators.http import require_http_methods
from django.conf import settings
import uuid
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect

logger = logging.getLogger(__name__)

def home_view(request):
    return render(request, 'pages/home.html')


def about_view(request):
    return render(request, 'pages/about.html')


def faq_view(request):
    return render(request, 'pages/faq.html')


def contact(request):
    """View for the contact page"""
    return render(request, 'pages/contact.html')


def terms_of_service(request):
    """View for the terms of service page"""
    return render(request, 'pages/terms_of_service.html')


def requisites_view(request):
    return render(request, 'pages/requisites.html')


def examples_view(request):
    service_history_section = {
        'title': 'История обслуживания у официального дилера',
        'subtitle': 'Доступны отчеты по более чем 20 маркам автомобилей из Европы, Америки, Азии, СНГ и РФ.',
        'icon': 'fas fa-history',
        'items': [
            {'name': 'Peugeot', 'url': static('img/examples/Peugeot.pdf')},
            {'name': 'Renault', 'url': static('img/examples/Renault.pdf')},
            {'name': 'Chrysler', 'url': static('img/examples/Chrysler.pdf')},
            {'name': 'Fiat', 'url': static('img/examples/Fiat.pdf')},
            {'name': 'Jaguar', 'url': static('img/examples/Jaguar.pdf')},
            {'name': 'Jeep', 'url': static('img/examples/Jeep.pdf')},
            {'name': 'Land Rover', 'url': static('img/examples/LandRover.pdf')},
            {'name': 'Lexus', 'url': static('img/examples/Lexus.pdf')},
            {'name': 'Mercedes-Benz', 'url': static('img/examples/Mercedes.pdf')},
            {'name': 'Nissan', 'url': static('img/examples/Nissan.pdf')},
            {'name': 'Opel', 'url': static('img/examples/Opel.pdf')},
            {'name': 'Toyota', 'url': static('img/examples/Toyota.pdf')},
            {'name': 'Mazda', 'url': static('img/examples/Mazda.pdf')},
            {'name': 'Ford', 'url': static('img/examples/Ford.pdf')},
            {'name': 'BMW', 'url': static('img/examples/BMW.pdf')},
            {'name': 'Audi', 'url': static('img/examples/AudiSeatSkodaVW.pdf')},
            {'name': 'Seat', 'url': static('img/examples/AudiSeatSkodaVW.pdf')},
            {'name': 'Skoda', 'url': static('img/examples/AudiSeatSkodaVW.pdf')},
            {'name': 'Volkswagen', 'url': static('img/examples/AudiSeatSkodaVW.pdf')},
            {'name': 'Porsche', 'url': static('img/examples/Porsche.pdf')},
        ]
    }
    
    car_equipment_section = {
        'title': 'Комплектация автомобиля',
        'subtitle': 'Подробная информация о заводской комплектации автомобиля.',
        'icon': 'fas fa-car',
        'items': [
            {'name': 'Audi', 'url': static('img/examples/audi_equipment.pdf')},
            {'name': 'BMW', 'url': static('img/examples/bmw_equipment.pdf')},
            {'name': 'Seat', 'url': static('img/examples/seat_skoda_vw_equipment.pdf')},
            {'name': 'Skoda', 'url': static('img/examples/seat_skoda_vw_equipment.pdf')},
            {'name': 'Volkswagen', 'url': static('img/examples/seat_skoda_vw_equipment.pdf')},
            {'name': 'Jaguar', 'url': static('img/examples/jaguar_equipment.pdf')},
            {'name': 'Landrover', 'url': static('img/examples/lendrover_equipment.pdf')},
            {'name': 'Mercedes-Benz', 'url': static('img/examples/mercedes_equipment.pdf')},
            {'name': 'Ford', 'url': static('img/examples/ford_equipment.pdf')},
            {'name': 'Porsche', 'url': static('img/examples/porshe_equipment.pdf')},
            {'name': 'Bentley', 'url': static('img/examples/bentley_equipment.pdf')},
        ]
    }
    
    carvertical_section = {
        'title': 'Отчеты Carvertical',
        'subtitle': 'Подробные отчеты о истории автомобиля от сервиса Carvertical.',
        'icon': 'fas fa-file-alt',
        'items': [
            {'name': 'Carvertical Audi', 'url': static('img/examples/audi_carvertical.pdf')},
            {'name': 'Carvertical BMW', 'url': static('img/examples/bmw_carvertical.pdf')},
            {'name': 'Carvertical Mercedes', 'url': static('img/examples/mercedes_carvertical.pdf')},
        ]
    }
    
    engine_number_section = {
        'title': 'Узнать номер двигателя по VIN',
        'subtitle': 'Уникальная возможность узнать заводской порядковый номер двигателя по VIN-коду.',
        'description': 'Результат приходит в виде фото или скриншота с дилерского ПК. Доступны марки: AUDI, VW, SKODA, SEAT, RENAULT, MERCEDES, VOLVO, OPEL, PEUGEOT, CITROEN, NISSAN, DODGE, JEEP, FIAT, KIA, HYUNDAI.',
        'icon': 'fas fa-cogs',
        'items': []
    }
    
    unlock_codes_section = {
        'title': 'Запрос кодов разблокировки по VIN',
        'subtitle': 'Получение кодов магнитол и другой электроники автомобиля.',
        'icon': 'fas fa-key',
        'items': [
            {'name': 'Запрос кода магнитолы для VAG по серийному номеру', 'url': static('img/examples/magnitola_vag.jpg')},
            {'name': 'Запрос кода SFD для VAG', 'url': static('img/examples/sfd_vag.pdf')},
            {'name': 'Запрос FSC (Freischaltcode) для BMW', 'url': static('img/examples/bmw_fsc.pdf')},
            {'name': 'Запрос кода магнитолы для Mercedes-Benz по серийному номеру', 'url': static('img/examples/magnitola_vag.jpg')},
        ]
    }
    
    service_campaigns_section = {
        'title': 'Проверка сервисных акций завода-изготовителя',
        'subtitle': 'Информация о сервисных акциях и отзывных кампаниях от производителя.',
        'description': 'Доступно для марок AUDI, VW, SEAT, SKODA, MERCEDES. Акции бывают разные: от обновления ПО до замены дорогостоящих узлов автомобиля. Выполняются бесплатно для владельца независимо от срока гарантии и количества владельцев.',
        'icon': 'fas fa-tools',
        'items': []
    }
    
    vehicle_checks_section = {
        'title': 'Проверка автомобиля по различным базам',
        'subtitle': 'Доступны проверки по следующим базам данных:',
        'icon': 'fas fa-search',
        'items': []
    }
    
    sections = [
        service_history_section,
        car_equipment_section,
        carvertical_section,
        engine_number_section,
        unlock_codes_section,
        service_campaigns_section,
        vehicle_checks_section
    ]
    
    context = {
        'sections': sections,
        'telegram_bot': 'Data_ViN_PR_bot'
    }
    
    return render(request, 'pages/examples.html', context)


def privacy_policy_view(request):
    return render(request, 'pages/privacy_policy.html')


def payment_rules_view(request):
    return render(request, 'pages/payment_rules.html')


def get_messages_view(request):
    request_types = [
        "запросил проверку Автотеки по vin",
        "запросил проверку Carfax Autocheck по vin",
        "запросил проверку Vinhistory по vin",
        "запросил проверку Аукционных лотов по vin",
        "Запрос полная история BMW",
        "Запрос полная история Mercedes-Benz",
        "Запрос полная история Audi",
        "Запрос полная история Volkswagen",
        "Запрос комплектации по vin",
        "Запрос сервисных акций"
    ]
    
    vin_numbers = [
        "WBA5W11040FJ41232",
        "X4XKJ79470LS32200",
        "WDD2040482A597143",
        "VF38BDHXE80424960",
        "XW7BF4FK40S037928",
        "WVWZZZ3CZGE509965",
        "WP0ZZZ99ZTS392124",
        "WAUZZZ8V9JA123456"
    ]
    
    messages = []
    now = datetime.now()
    
    for i in range(10):
        time_ago = now - timedelta(minutes=random.randint(1, 60))
        timestamp = time_ago.strftime('%d-%m-%y %H:%M:%S')
        
        if random.choice([True, False]):
            source = "Пользователь бота @Data_ViN_PR_bot"
        else:
            source = "Пользователь сайта"
        
        request_type = random.choice(request_types)
        vin = random.choice(vin_numbers)
        
        message = f"{timestamp} {source} {request_type} {vin}"
        messages.append(message)
    
    messages.sort(reverse=True)
    
    return HttpResponse("\n".join(messages))


def check_autoteka_view(request):
    """API endpoint for checking vehicle data in Autoteka database (VIN, Reg Number, Avito Link)."""
    # Handle both GET and POST requests
    if request.method == 'POST':
        try:
            # Debugging - log the raw request body
            logger.debug(f"POST Autoteka raw request body: {request.body.decode('utf-8', errors='replace')}")
            
            # Check content type to determine how to parse the data
            content_type = request.headers.get('Content-Type', '')
            logger.debug(f"POST content type: {content_type}")
            
            if 'application/json' in content_type:
                # JSON data
                data = json.loads(request.body)
                logger.debug(f"POST Autoteka parsed JSON: {data}")
            else:
                # Assume form data
                data = {}
                for key in request.POST:
                    data[key] = request.POST[key]
                logger.debug(f"POST Autoteka form data: {data}")
            
            # The frontend might be sending the data in different formats
            # Check all possible parameter names
            input_value = None
            for key in ['input', 'vin', 'gov_number', 'avito_link', 'vin_input']:
                if key in data:
                    input_value = data[key]
                    logger.debug(f"Found input value in key: {key} = {input_value}")
                    break
            
            # If no specific type is provided, infer it from the key used
            if 'type' in data:
                input_type = data['type']
            else:
                # Try to infer type from which parameter was provided
                if 'vin' in data:
                    input_type = 'vin'
                elif 'gov_number' in data:
                    input_type = 'gov_number'
                elif 'avito_link' in data:
                    input_type = 'avito_link'
                else:
                    # Default
                    input_type = 'vin'
                    
            logger.debug(f"POST Autoteka check with: value={input_value}, type={input_type}")
                
        except (JSONDecodeError, ValueError) as e:
            logger.exception(f"Error parsing JSON in POST Autoteka request: {e}")
            return JsonResponse({"error": "Некорректный формат JSON"}, status=400)
    else:  # GET request
        input_value = request.GET.get("input")
        input_type = request.GET.get("type", 'vin')  # Default to 'vin' if type not provided
    
    # Validate input
    if not input_value:
        logger.warning(f"Autoteka check failed: Missing 'input' parameter. Method: {request.method}")
        if request.method == 'POST':
            logger.warning(f"POST data keys: {list(data.keys()) if 'data' in locals() else 'No data parsed'}")
        return JsonResponse({
            "error": "Необходимо указать значение для проверки (VIN, госномер, ссылка)",
            "message": "Для проверки используйте параметр 'input' или 'vin'"
        }, status=400)
    
    # Map input types to service types
    type_mapping = {
        'vin': 'vin',
        'gov_number': 'regNumber',  # For backward compatibility with old code
        'reg_number': 'regNumber',
        'regNumber': 'regNumber',
        'avito_link': 'itemId'      # Avito links get converted to itemId
    }
    
    if input_type not in type_mapping:
        valid_types = list(type_mapping.keys())
        logger.warning(f"Autoteka check failed: Invalid 'type' parameter: {input_type}")
        return JsonResponse({
            "error": f"Некорректный тип запроса: {input_type}. Допустимые типы: {valid_types}"
        }, status=400)

    # Prepare input and cache key based on type
    service_type = type_mapping[input_type]
    
    if input_type == 'avito_link':
        avito_id = extract_avito_id(input_value)
        if not avito_id:
            logger.warning(f"Autoteka check failed: Could not extract Avito ID from URL: {input_value}")
            return JsonResponse({
                "error": "Не удалось извлечь ID объявления из ссылки Avito"
            }, status=400)
        service_input = avito_id
        cache_key = generate_cache_key("autoteka", input_type, avito_id)
    else:  # vin or regNumber
        service_input = input_value.upper()  # Normalize
        cache_key = generate_cache_key("autoteka", input_type, service_input)
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"[Cache HIT] Returning cached Autoteka data for {input_type}:{service_input}")
        return JsonResponse(cached_data)

    logger.info(f"[Cache MISS] Requesting Autoteka check for {input_type}:{service_input}")
    
    # Call service function with the right parameters
    try:
        result = check_autoteka(service_input, service_type)
        
        # Handle case where service returns a direct error result
        if not result:
            logger.error(f"Autoteka check failed: No result returned for {input_type}:{service_input}")
            return JsonResponse({
                "error": "Ошибка при проверке данных в Автотеке. Пожалуйста, попробуйте позже."
            }, status=500)
            
        # Determine cache TTL based on result (cache errors/not found shorter)
        ttl = CACHE_TIME_LONG if result.get("success") else CACHE_TIME_SHORT
        cache.set(cache_key, result, ttl)
        logger.info(f"[Cache SET] Stored Autoteka result for {input_type}:{service_input} with TTL: {ttl}s")
        
        # Return the result
        return JsonResponse(result)
        
    except Exception as e:
        logger.exception(f"Unexpected error during Autoteka check view for {input_type}:{service_input}: {e}")
        return JsonResponse({
            "error": "Произошла ошибка при проверке данных. Пожалуйста, попробуйте позже."
        }, status=500)


def check_carfax_view(request):
    """API endpoint for checking vehicle data in Carfax/Autocheck (via Carstat)."""
    # Handle both GET and POST requests
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            vin_input = data.get('vin') or data.get('input')
        except (JSONDecodeError, ValueError) as e:
            logger.exception(f"Error parsing JSON in POST Carfax request: {e}")
            return JsonResponse({"error": "Некорректный формат JSON"}, status=400)
    else:  # GET request
        vin_input = request.GET.get("input")
    
    if not vin_input:
        logger.warning("Carfax check failed: Missing 'input' (VIN) parameter.")
        return JsonResponse({"error": "Необходимо указать VIN"}, status=400)

    vin_upper = vin_input.upper()
    if len(vin_upper) != 17:
         logger.warning(f"Carfax check failed: Invalid VIN length: {len(vin_upper)}")
         return JsonResponse({"error": "VIN должен состоять из 17 символов"}, status=400)

    cache_key = generate_cache_key("carfax_autocheck", vin_upper)

    # Check cache
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"[Cache HIT] Returning cached Carfax/Autocheck data for VIN: {vin_upper}")
        return JsonResponse(cached_data)

    logger.info(f"[Cache MISS] Requesting Carfax/Autocheck check for VIN: {vin_upper}")
    # Call service function
    try:
        result = check_carfax_autocheck(vin_upper)
        
        # Cache result
        ttl = CACHE_TIME_LONG if result.get("success") else CACHE_TIME_SHORT
        cache.set(cache_key, result, ttl)
        logger.info(f"[Cache SET] Stored Carfax/Autocheck result for VIN: {vin_upper} with TTL: {ttl}s")
        
        return JsonResponse(result)
    except Exception as e:
        logger.exception(f"Unexpected error during Carfax check for VIN: {vin_upper}: {e}")
        return JsonResponse({"error": "Произошла ошибка при проверке данных"}, status=500)


def check_vinhistory_view(request):
    """API endpoint for checking vehicle data in Vinhistory database."""
    # Handle both GET and POST requests
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            vin_input = data.get('vin') or data.get('input')
        except (JSONDecodeError, ValueError) as e:
            logger.exception(f"Error parsing JSON in POST VINHistory request: {e}")
            return JsonResponse({"error": "Некорректный формат JSON"}, status=400)
    else:  # GET request
        vin_input = request.GET.get("input")
    
    if not vin_input:
        logger.warning("Vinhistory check failed: Missing 'input' (VIN) parameter.")
        return JsonResponse({"error": "Необходимо указать VIN"}, status=400)
        
    vin_upper = vin_input.upper()
    if len(vin_upper) != 17:
         logger.warning(f"Vinhistory check failed: Invalid VIN length: {len(vin_upper)}")
         return JsonResponse({"error": "VIN должен состоять из 17 символов"}, status=400)

    cache_key = generate_cache_key("vinhistory", vin_upper)

    # Check cache
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"[Cache HIT] Returning cached Vinhistory data for VIN: {vin_upper}")
        return JsonResponse(cached_data)
        
    logger.info(f"[Cache MISS] Requesting Vinhistory check for VIN: {vin_upper}")
    # Call service function
    try:
        result = check_vinhistory(vin_upper)
        
        # Cache result
        ttl = CACHE_TIME_SHORT # Cache Vinhistory shorter based on previous service logic, adjust if needed
        cache.set(cache_key, result, ttl)
        logger.info(f"[Cache SET] Stored Vinhistory result for VIN: {vin_upper} with TTL: {ttl}s")
        
        return JsonResponse(result)
    except Exception as e:
        logger.exception(f"Unexpected error during VINHistory check for VIN: {vin_upper}: {e}")
        return JsonResponse({"error": "Произошла ошибка при проверке данных"}, status=500)


def check_auction_view(request):
    """API endpoint for checking vehicle auction lots (via Carstat)."""
    # Handle both GET and POST requests
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            vin_input = data.get('vin') or data.get('input')
        except (JSONDecodeError, ValueError) as e:
            logger.exception(f"Error parsing JSON in POST auction request: {e}")
            return JsonResponse({"error": "Некорректный формат JSON"}, status=400)
    else:  # GET request
        vin_input = request.GET.get("input")
    
    if not vin_input:
        logger.warning("Auction check failed: Missing 'input' (VIN) parameter.")
        return JsonResponse({"error": "Необходимо указать VIN"}, status=400)

    vin_upper = vin_input.upper()
    if len(vin_upper) != 17:
         logger.warning(f"Auction check failed: Invalid VIN length: {len(vin_upper)}")
         return JsonResponse({"error": "VIN должен состоять из 17 символов"}, status=400)

    cache_key = generate_cache_key("auction", vin_upper)

    # Check cache
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"[Cache HIT] Returning cached Auction data for VIN: {vin_upper}")
        return JsonResponse(cached_data)

    logger.info(f"[Cache MISS] Requesting Auction check for VIN: {vin_upper}")
    # Call service function
    try:
        result = check_auction(vin_upper)
        
        # Cache result
        ttl = CACHE_TIME_LONG if result.get("success") else CACHE_TIME_SHORT
        cache.set(cache_key, result, ttl)
        logger.info(f"[Cache SET] Stored Auction result for VIN: {vin_upper} with TTL: {ttl}s")

        return JsonResponse(result)
    except Exception as e:
        logger.exception(f"Unexpected error during auction check for VIN: {vin_upper}: {e}")
        return JsonResponse({"error": "Произошла ошибка при проверке данных"}, status=500)


def generate_avito_token():
    """Generate and cache a new Avito token."""
    token = get_avito_token()
    if token:
        return {"success": True, "message": "Токен Avito успешно получен и кэширован."}
    else:
        return {"success": False, "message": "Не удалось получить токен Avito. Проверьте настройки и логи."}


@require_GET
def debug_api_view(request):
    """View for checking API configuration (admin only)"""
    # Basic security check - allow only superusers or in DEBUG mode
    if not (request.user.is_superuser or settings.DEBUG):
        return HttpResponse("Access denied. This page requires administrator privileges.", status=403)
    
    # Check for token refresh action
    if request.GET.get('refresh_token') == '1':
        token_result = generate_avito_token()
        if token_result["success"]:
            messages.success(request, token_result["message"])
        else:
            messages.error(request, token_result["message"])
        # Redirect to remove the query parameter
        return HttpResponseRedirect(reverse('pages:debug_api'))
    
    # Test caching
    cache_test_key = f"debug_test_{uuid.uuid4()}"
    cache_test_value = "test_value"
    cache.set(cache_test_key, cache_test_value, 60)
    cache_working = cache.get(cache_test_key) == cache_test_value
    
    # Get cache backend info
    cache_backend = str(settings.CACHES['default']['BACKEND']).split('.')[-1]
    
    # Check Avito/Autoteka configuration
    avito_token_url = getattr(settings, 'AVITO_TOKEN_URL', None)
    avito_client_id = getattr(settings, 'AVITO_CLIENT_ID', None)
    avito_client_secret = getattr(settings, 'AVITO_CLIENT_SECRET', None)
    avito_status = all([
        avito_token_url,
        avito_client_id and avito_client_id != "client_id_here",
        avito_client_secret and avito_client_secret != "client_secret_here"
    ])
    avito_token_cached = bool(cache.get("avito_token"))
    
    # Check Carstat configuration
    carstat_api_key = getattr(settings, 'CARSTAT_API_KEY', None)
    carstat_status = bool(carstat_api_key and len(carstat_api_key) > 10)
    
    # Check VINHistory configuration
    vinhistory_login = getattr(settings, 'VINHISTORY_LOGIN', None)
    vinhistory_pass = getattr(settings, 'VINHISTORY_PASS', None)
    vinhistory_status = bool(vinhistory_login and vinhistory_pass)
    
    context = {
        'avito_token_url': avito_token_url,
        'avito_client_id': avito_client_id is not None,
        'avito_client_secret': avito_client_secret is not None,
        'avito_status': avito_status,
        'avito_token_cached': avito_token_cached,
        
        'carstat_api_key': carstat_api_key is not None,
        'carstat_status': carstat_status,
        
        'vinhistory_login': vinhistory_login is not None,
        'vinhistory_pass': vinhistory_pass is not None,
        'vinhistory_status': vinhistory_status,
        
        'cache_backend': cache_backend,
        'cache_working': cache_working,
    }
    
    return render(request, 'pages/debug.html', context)
