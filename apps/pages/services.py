import time
import requests
import logging
import json
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from urllib.parse import urlparse, parse_qs
import os
from typing import Dict, Any, Union, Optional
import traceback

logger = logging.getLogger(__name__)

# Settings for external APIs
AUTOTEKA_URLS = {
    "vin": "https://pro.autoteka.ru/autoteka/v1/previews",
    "regNumber": "https://pro.autoteka.ru/autoteka/v1/request-preview-by-regnumber",
    "itemId": "https://pro.autoteka.ru/autoteka/v1/request-preview-by-item-id",
    "preview_url": "https://pro.autoteka.ru/autoteka/v1/previews"
}

AVITO_TOKEN_URL = settings.AVITO_TOKEN_URL
AVITO_CLIENT_ID = settings.AVITO_CLIENT_ID
AVITO_CLIENT_SECRET = settings.AVITO_CLIENT_SECRET

CARSTAT_API_KEY = settings.CARSTAT_API_KEY
CARSTAT_BASE_URL = "https://carstat.dev/api"

VINHISTORY_URL = "https://vinhistory.ru/api/search"
VINHISTORY_LOGIN = settings.VINHISTORY_LOGIN
VINHISTORY_PASS = settings.VINHISTORY_PASS

# Cache TTL - 24 hours
CACHE_TTL = 86400

# Cache times (in seconds)
CACHE_TIME_SHORT = 3600  # 1 hour
CACHE_TIME_LONG = 86400  # 24 hours

def generate_cache_key(prefix: str, *args: Any) -> str:
    """Generate a unique cache key."""
    key_parts = [str(arg) for arg in args]
    return f"{prefix}:" + ":".join(key_parts)

def log_check_request(check_type: str, identifier: str) -> str:
    """Log vehicle check requests for analytics"""
    message = f"{datetime.now().strftime('%d-%m-%y %H:%M:%S')} User requested {check_type} check for {identifier}"
    logger.info(message)
    return message

def get_avito_token() -> Optional[str]:
    """
    Get authentication token for Avito/Autoteka API with Django caching.
    """
    cache_key = "avito_token"
    token = cache.get(cache_key)
    if token:
        logger.debug("Retrieved Avito token from cache.")
        return token

    # Check if credentials are set properly and not placeholder values
    if not AVITO_CLIENT_ID or AVITO_CLIENT_ID == "client_id_here" or not AVITO_CLIENT_SECRET or AVITO_CLIENT_SECRET == "client_secret_here":
        logger.error("Avito credentials not configured properly. Check AVITO_CLIENT_ID and AVITO_CLIENT_SECRET in settings.")
        return None

    logger.info("Fetching new Avito token.")
    try:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(
            AVITO_TOKEN_URL,
            headers=headers,
            data={
                "grant_type": "client_credentials",
                "client_id": AVITO_CLIENT_ID,
                "client_secret": AVITO_CLIENT_SECRET
            },
            timeout=10 # Standard timeout
        )
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        token_data = response.json()
        token = token_data.get('access_token')
        if not token:
            logger.error("No access_token found in Avito response.")
            return None

        # Cache token with expiration time - 60 second buffer
        expires_in = token_data.get('expires_in', 3600) - 60
        cache.set(cache_key, token, timeout=max(60, expires_in)) # Ensure timeout is positive
        logger.info(f"Successfully fetched and cached new Avito token. Expires in {expires_in}s.")
        return token

    except requests.exceptions.RequestException as e:
        logger.exception(f"HTTP error getting Avito token: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error getting Avito token: {e}")
        return None

def extract_avito_id(url: str) -> str:
    """Extract item ID from Avito URL"""
    try:
        parsed = urlparse(url)
        if "avito.ru" not in parsed.netloc:
            return ""
        
        # For URLs like https://www.avito.ru/.../_123456789
        if "_" in parsed.path:
            return parsed.path.split("_")[-1]
        
        # Try to extract from query parameters
        query_params = parse_qs(parsed.query)
        if "id" in query_params:
            return query_params["id"][0]
        
        return ""
    except Exception as e:
        logger.exception(f"Error extracting Avito ID from URL: {str(e)}")
        return ""

def check_autoteka(input_value: str, input_type: str) -> Dict[str, Any]:
    """
    Check vehicle information in Autoteka database using real API calls.

    Args:
        input_value: VIN, license plate, or Avito item ID.
        input_type: Type of input ('vin', 'regNumber', 'itemId').

    Returns:
        Dict with results of the check or an error message.
    """
    # Validate input parameters
    if not input_value:
        logger.error("Empty input_value provided to check_autoteka")
        return {"error": "Необходимо указать значение для проверки"}

    if input_type not in ('vin', 'regNumber', 'itemId'):
        logger.error(f"Invalid input_type provided to check_autoteka: {input_type}")
        return {"error": f"Неверный тип запроса: {input_type}. Допустимы: vin, regNumber, itemId"}

    # Normalize input based on type
    if input_type in ('vin', 'regNumber'):
        cache_key_val = input_value.upper() # Normalize VIN/RegNumber
    elif input_type == 'itemId':
        try:
            # Ensure itemId is numeric
            cache_key_val = str(int(input_value))
        except ValueError:
            logger.error(f"Invalid itemId format for Autoteka check: {input_value}")
            return {"error": "ID объявления Avito должен быть числом"}
    else:
        cache_key_val = input_value

    cache_key = generate_cache_key("autoteka", input_type, cache_key_val)
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"Retrieved Autoteka data from cache for {input_type}:{cache_key_val}")
        return cached_result

    log_check_request("Autoteka", f"{input_type} {cache_key_val}")

    # Get API token
    access_token = get_avito_token()
    if not access_token:
        logger.error("Failed to get Avito token for Autoteka check")
        return {"error": "Ошибка авторизации в Автотеке. Пожалуйста, обратитесь к администратору."}

    # Define headers EXACTLY as needed for the preview request
    preview_request_headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    # Headers for the status polling (might just need Authorization)
    status_polling_headers = {'Authorization': f'Bearer {access_token}'}

    try:
        # Determine API endpoint and payload based on input type, matching working Flask code
        if input_type == 'vin':
            preview_url = AUTOTEKA_URLS["vin"] # Endpoint: /previews
            payload = {"vin": cache_key_val}
        elif input_type == 'regNumber':
            preview_url = AUTOTEKA_URLS["regNumber"] # Endpoint: /request-preview-by-regnumber
            payload = {"regNumber": cache_key_val}
        elif input_type == 'itemId':
            preview_url = AUTOTEKA_URLS["itemId"] # Endpoint: /request-preview-by-item-id
            try:
                item_id = int(cache_key_val)
                payload = {"itemId": item_id}
            except ValueError:
                logger.error(f"Invalid itemId format: {cache_key_val}")
                return {"error": "Некорректный ID объявления Авито"}
        else:
            # This case should not be reached due to validation in the view
            logger.error(f"Invalid input_type for Autoteka check: {input_type}")
            return {"error": "Некорректный тип запроса для Автотеки"}

        # 1. Request preview ID
        logger.info(f"Requesting Autoteka preview for {input_type}: {cache_key_val} at URL: {preview_url}")
        # logger.debug(f"Autoteka Request URL: {preview_url}") # Already logged above
        logger.debug(f"Autoteka Request Headers: {preview_request_headers}")
        logger.debug(f"Autoteka Request Payload: {json.dumps(payload)}")
        try:
            response = requests.post(preview_url, headers=preview_request_headers, json=payload, timeout=(5, 15))
            logger.debug(f"Autoteka Response Status Code: {response.status_code}")
            logger.debug(f"Autoteka Response Text: {response.text}")
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error_text = e.response.text
            logger.exception(f"HTTP error during Autoteka preview POST: {status_code}, {error_text}")

            if status_code == 401 or status_code == 403:
                # Invalidate token cache on auth errors
                cache.delete("avito_token")
                logger.warning("Avito token seems invalid, cache cleared.")
                return {"error": "Ошибка авторизации в Автотеке. Проверьте учетные данные или обновите токен."}
            elif status_code == 404:
                # 404 on POST likely means bad endpoint/parameters, not necessarily 'VIN not found'
                return {"error": f"Ошибка API Автотеки (404 - Not Found). Возможно, неверный URL или параметры запроса."}
            else:
                return {"error": f"Ошибка сервера Автотеки ({status_code}) при запросе previewId. Попробуйте позже."}
        except requests.exceptions.RequestException as e:
            logger.exception(f"Request error during Autoteka check: {e}")
            return {"error": "Ошибка соединения с сервером Автотеки. Проверьте подключение к интернету."}
        
        # Parse the response for preview ID
        try:
            preview_data = response.json()
        except json.JSONDecodeError:
            logger.exception(f"Invalid JSON in Autoteka response: {response.text}")
            return {"error": "Некорректный ответ от сервера Автотеки. Попробуйте позже."}

        # Extract preview ID
        preview_id = preview_data.get('result', {}).get('preview', {}).get('previewId')
        if not preview_id:
            logger.error(f"No previewId in Autoteka response: {preview_data}")
            
            # Check if the API returned a specific status like "notFound" directly
            status = preview_data.get('result', {}).get('preview', {}).get('status')
            if status == 'notFound':
                # Use success: False structure consistent with polling results
                result = {"success": False, "message": f'❌ {cache_key_val} отсутствует в Автотеке'}
                cache.set(cache_key, result, CACHE_TIME_SHORT)
                return result
            
            return {"error": "Не удалось получить данные от Автотеки. Попробуйте позже."}

        # 2. Poll for status
        # Use the v1 preview URL base for status polling
        status_url = f"{AUTOTEKA_URLS['preview_url']}/{preview_id}"
        max_wait_time = 120  # seconds
        poll_interval = 3    # seconds
        elapsed_time = 0

        logger.info(f"Polling Autoteka status for previewId: {preview_id}")
        while elapsed_time < max_wait_time:
            time.sleep(poll_interval)
            elapsed_time += poll_interval

            try:
                logger.debug(f"Polling Autoteka status URL: {status_url}")
                logger.debug(f"Polling Autoteka status Headers: {status_polling_headers}")
                status_response = requests.get(status_url, headers=status_polling_headers, timeout=(5, 15))
                logger.debug(f"Polling Autoteka status Response Code: {status_response.status_code}")
                logger.debug(f"Polling Autoteka status Response Text: {status_response.text}")
                status_response.raise_for_status()
                status_data = status_response.json()

                status = status_data.get('result', {}).get('preview', {}).get('status')
                logger.debug(f"Autoteka status check for {preview_id}: {status}")

                if status == 'success':
                    preview_content = status_data.get('result', {}).get('preview', {})
                    brand = preview_content.get('data', {}).get('brand')
                    model = preview_content.get('data', {}).get('model')
                    year = preview_content.get('data', {}).get('year')

                    # Construct a more informative success message
                    result = {
                        "success": True,
                        "message": "Данные найдены в Автотеке.",
                        "data": {
                            "VIN/ГН/Id": cache_key_val,
                            "Марка": brand,
                            "Модель": model,
                            "Год": year
                        }
                    }
                    logger.info(f"Autoteka check successful for {input_type}:{cache_key_val}")
                    cache.set(cache_key, result, CACHE_TIME_LONG)
                    return result

                elif status == 'processing':
                    logger.debug(f"Autoteka report for {preview_id} still processing...")
                    continue # Keep polling

                elif status == 'notFound':
                    logger.info(f"Autoteka check result: {cache_key_val} not found.")
                    result = {"success": False, "message": f'❌ {cache_key_val} отсутствует в Автотеке'}
                    cache.set(cache_key, result, CACHE_TIME_SHORT) # Cache not found results shorter
                    return result

                elif status == 'error':
                    error_details = status_data.get('result', {}).get('preview', {}).get('error', {})
                    logger.error(f"Autoteka processing error for {preview_id}: {error_details}")
                    result = {"error": "Ошибка обработки данных в Автотеке."}
                    cache.set(cache_key, result, CACHE_TIME_SHORT)
                    return result
                
                elif status == 'reportNotFound': # Handle specific 'reportNotFound' status if it exists
                    logger.info(f"Autoteka report not found for {preview_id}. VIN: {cache_key_val}")
                    result = {"success": False, "message": f'❌ Отчет Автотеки для {cache_key_val} не найден'}
                    cache.set(cache_key, result, CACHE_TIME_SHORT)
                    return result

                else:
                    logger.warning(f"Unknown Autoteka status for {preview_id}: {status}. Data: {status_data}")
                    # Continue polling unless it's clearly a final state

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                error_text = e.response.text
                logger.exception(f"HTTP error polling Autoteka status for {preview_id}: {status_code}, {error_text}")
                # Don't cache intermittent polling errors, but stop polling if it's auth related
                if status_code == 401 or status_code == 403:
                    cache.delete("avito_token")
                    logger.warning("Avito token seems invalid during polling, cache cleared.")
                    return {"error": "Ошибка авторизации в Автотеке во время проверки статуса."}
                # Retry on other server errors? For now, stop polling and return error.
                return {"error": f"Ошибка сервера Автотеки ({status_code}) при проверке статуса."}
            except requests.exceptions.RequestException as e:
                logger.exception(f"Request error polling Autoteka status for {preview_id}: {e}")
                # Stop polling on connection errors
                return {"error": "Ошибка соединения с сервером Автотеки при проверке статуса."}
            except json.JSONDecodeError:
                logger.exception(f"Invalid JSON in Autoteka status response: {status_response.text}")
                return {"error": "Некорректный ответ от сервера Автотеки при проверке статуса."}

        # If loop finishes without a result
        logger.warning(f"Autoteka check timed out for {preview_id} ({input_type}:{cache_key_val})")
        return {"error": "Превышено время ожидания ответа от Автотеки"}

    except Exception as e:
        logger.exception(f"Unexpected error during Autoteka check for {input_type}:{cache_key_val}: {e}")
        return {"error": "Непредвиденная ошибка при проверке Автотеки"}

def check_carfax_autocheck(vin: str) -> Dict[str, Any]:
    """
    Check vehicle information in Carfax and Autocheck via Carstat API.

    Args:
        vin: Vehicle Identification Number (should be 17 chars).

    Returns:
        Dict with results of the check or an error message.
    """
    vin_upper = vin.upper()
    if not vin or len(vin_upper) != 17:
         return {"error": "VIN должен состоять из 17 символов"}

    # Check if API key is set properly
    if not CARSTAT_API_KEY or len(CARSTAT_API_KEY) < 10:
        logger.error("Carstat API key not configured properly. Check CARSTAT_API_KEY in settings.")
        return {"error": "Ошибка настройки API ключа Carstat. Пожалуйста, обратитесь к администратору."}

    cache_key = generate_cache_key("carfax_autocheck", vin_upper)
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"Retrieved Carfax/Autocheck data from cache for {vin_upper}")
        return cached_result

    log_check_request("Carfax/Autocheck", vin_upper)
    url = f'{CARSTAT_BASE_URL}/reports/check-records/{vin_upper}'
    headers = {'accept': '*/*', 'x-api-key': CARSTAT_API_KEY}

    try:
        logger.info(f"Checking Carfax/Autocheck (Carstat) for {vin_upper}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        vehicle_info = data.get('vehicle')
        carfax_records = data.get('carfax')
        autocheck_records = data.get('autocheck')

        # Check if data is meaningful
        has_records = (carfax_records is not None and carfax_records > 0) or \
                      (autocheck_records is not None and autocheck_records > 0)
        is_valid_vehicle = vehicle_info and vehicle_info.lower() not in ('null null', 'null null 0')

        if has_records and is_valid_vehicle:
            result = {
                "success": True,
                "vehicle_info": vehicle_info,
                "carfax_records": carfax_records,
                "autocheck_records": autocheck_records,
                "message": f"✅ Найдены записи для {vehicle_info}"
            }
            logger.info(f"Carfax/Autocheck check successful for {vin_upper}")
        else:
            logger.info(f"No Carfax/Autocheck records found for {vin_upper}")
            result = {"message": f"❌ VIN {vin_upper} отсутствует в базах Carfax/Autocheck"}

        cache.set(cache_key, result, CACHE_TIME_LONG)
        return result

    except requests.exceptions.HTTPError as e:
        logger.exception(f"HTTP error during Carfax/Autocheck check for {vin_upper}. Status: {e.response.status_code}, Response: {e.response.text}")
        # Handle specific Carstat errors if known, e.g., 404 for not found
        if e.response.status_code == 404:
             result = {"message": f"❌ VIN {vin_upper} не найден в Carstat"}
             cache.set(cache_key, result, CACHE_TIME_SHORT)
             return result
        return {"error": f"Ошибка сети при запросе к Carstat ({e.response.status_code})"}
    except requests.exceptions.RequestException as e:
        logger.exception(f"Request error during Carfax/Autocheck check for {vin_upper}: {e}")
        return {"error": "Ошибка сети при запросе к Carstat. Проверьте подключение к интернету."}
    except Exception as e:
        logger.exception(f"Unexpected error during Carfax/Autocheck check for {vin_upper}: {e}")
        return {"error": "Внутренняя ошибка при проверке Carfax/Autocheck. Пожалуйста, попробуйте позже."}

def check_vinhistory(vin: str) -> Dict[str, Any]:
    """
    Check vehicle information in Vinhistory database.

    Args:
        vin: The Vehicle Identification Number.

    Returns:
        Dict with results of the check or an error message.
    """
    if not vin:
        logger.error("Empty VIN provided to check_vinhistory")
        return {"error": "Необходимо указать VIN"}

    vin_upper = vin.upper()
    if len(vin_upper) != 17:
        logger.warning(f"Invalid VIN length for Vinhistory check: {len(vin_upper)}")
        return {"error": "VIN должен состоять из 17 символов"}

    cache_key = generate_cache_key("vinhistory", vin_upper)
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"Retrieved Vinhistory data from cache for VIN: {vin_upper}")
        return cached_result

    log_check_request("Vinhistory", vin_upper)

    if not VINHISTORY_LOGIN or not VINHISTORY_PASS:
        logger.error("VINHistory credentials not configured properly.")
        return {"error": "Ошибка конфигурации сервиса Vinhistory."}

    params = {"login": VINHISTORY_LOGIN, "password": VINHISTORY_PASS, "vin": vin_upper}

    try:
        logger.info(f"Checking Vinhistory for {vin_upper}")
        response = requests.get(VINHISTORY_URL, params=params, timeout=15)
        response.raise_for_status() # Raise HTTPError for bad responses

        data = response.json()

        # Extract relevant data, similar to Flask example
        vehicle_data = data.get('vehicle', {})
        images_count = data.get('images', 0)
        
        vehicle_make = vehicle_data.get('make')
        vehicle_model = vehicle_data.get('model')
        vehicle_year = vehicle_data.get('year')

        # Check if actual data exists and there are images
        if images_count > 0 and vehicle_make and vehicle_model and vehicle_year:
            logger.info(f"Vinhistory found {images_count} images for {vin_upper}")
            result = {
                "success": True,
                "message": "Данные найдены в Vinhistory.",
                "data": {
                    "✅ Данные ": f"{vehicle_make} {vehicle_model} {vehicle_year}",
                    "VIN": vin_upper,
                    "📍Кол-во фото в отчете:": images_count
                }
            }
            ttl = CACHE_TIME_LONG
        # Handle case where VIN might be found but has no images (or incomplete data)
        elif vehicle_make and vehicle_model and vehicle_year:
             logger.info(f"Vinhistory found vehicle data but no images for {vin_upper}")
             # Return a slightly different message indicating data exists but no images
             result = {
                 "success": True, # Still technically a success, but with nuance
                 "message": "Данные об автомобиле найдены, но фото отсутствуют.",
                 "data": {
                     "✅ Данные ": f"{vehicle_make} {vehicle_model} {vehicle_year}",
                     "VIN": vin_upper,
                     "📍Кол-во фото в отчете:": 0
                 }
             }
             ttl = CACHE_TIME_SHORT # Cache less time if no images? Or use LONG? Let's use SHORT for now.
        else:
            # VIN not found or incomplete data returned
            logger.info(f"No complete Vinhistory data found for {vin_upper}")
            result = {"success": False, "message": f"❌ В базе данных Vinhistory отсутствует VIN {vin_upper}"}
            ttl = CACHE_TIME_SHORT # Cache not found results shorter

        cache.set(cache_key, result, ttl)
        logger.info(f"Stored Vinhistory result for VIN: {vin_upper} with TTL: {ttl}s")
        return result

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_text = e.response.text
        logger.exception(f"HTTP error during Vinhistory check for {vin_upper}: {status_code}, {error_text}")
        # Check for specific errors if needed, e.g., bad credentials
        if status_code == 401 or status_code == 403:
             return {"error": "Ошибка авторизации в Vinhistory. Проверьте учетные данные."}
        return {"error": f"Ошибка сервера Vinhistory ({status_code}). Попробуйте позже."}
    except requests.exceptions.RequestException as e:
        logger.exception(f"Request error during Vinhistory check for {vin_upper}: {e}")
        return {"error": "Ошибка соединения с сервером Vinhistory."}
    except json.JSONDecodeError:
        logger.exception(f"Invalid JSON in Vinhistory response: {response.text}")
        return {"error": "Некорректный ответ от сервера Vinhistory."}
    except Exception as e:
        logger.exception(f"Unexpected error during Vinhistory check for {vin_upper}: {e}")
        return {"error": "Непредвиденная ошибка при проверке Vinhistory"}

def check_auction(vin: str) -> Dict[str, Any]:
    """
    Check vehicle auction history using Carstat API.

    Args:
        vin: Vehicle Identification Number (should be 17 chars).

    Returns:
        Dict with results of the check or an error message.
    """
    vin_upper = vin.upper()
    if not vin or len(vin_upper) != 17:
        return {"error": "VIN должен состоять из 17 символов"}

    # Check if API key is set properly
    if not CARSTAT_API_KEY or len(CARSTAT_API_KEY) < 10:
        logger.error("Carstat API key not configured properly. Check CARSTAT_API_KEY in settings.")
        return {"error": "Ошибка настройки API ключа Carstat. Пожалуйста, обратитесь к администратору."}

    cache_key = generate_cache_key("auction", vin_upper)
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"Retrieved auction data (Carstat) from cache for {vin_upper}")
        return cached_result

    log_check_request("Auction (Carstat)", vin_upper)
    url = f'{CARSTAT_BASE_URL}/local-exists/{vin_upper}'
    headers = {'accept': '*/*', 'x-api-key': CARSTAT_API_KEY}

    try:
        logger.info(f"Checking auction history (Carstat) for {vin_upper}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get('exists'):
            # The 'domains' list seems to indicate individual auction records/sources
            auction_records_count = len(data.get('domains', []))
            result = {
                "success": True,
                "auction_records_count": auction_records_count,
                 "message": f"✅ Найдены записи об аукционах ({auction_records_count} шт.) для VIN {vin_upper}"
            }
            logger.info(f"Auction check (Carstat) successful for {vin_upper}")
        else:
            logger.info(f"No auction records (Carstat) found for {vin_upper}")
            result = {"message": f"❌ VIN {vin_upper} отсутствует в базе аукционов Carstat"}

        cache.set(cache_key, result, CACHE_TIME_LONG)
        return result

    except requests.exceptions.HTTPError as e:
        logger.exception(f"HTTP error during auction check (Carstat) for {vin_upper}. Status: {e.response.status_code}, Response: {e.response.text}")
        # Handle specific Carstat errors if known, e.g., 404
        if e.response.status_code == 404:
             result = {"message": f"❌ VIN {vin_upper} не найден в базе аукционов Carstat"}
             cache.set(cache_key, result, CACHE_TIME_SHORT)
             return result
        return {"error": f"Ошибка сети при запросе к Carstat (аукционы) ({e.response.status_code})"}
    except requests.exceptions.RequestException as e:
        logger.exception(f"Request error during auction check (Carstat) for {vin_upper}: {e}")
        return {"error": "Ошибка сети при запросе к Carstat (аукционы). Проверьте подключение к интернету."}
    except Exception as e:
        logger.exception(f"Unexpected error during auction check (Carstat) for {vin_upper}: {e}")
        return {"error": "Внутренняя ошибка при проверке истории аукционов. Пожалуйста, попробуйте позже."} 