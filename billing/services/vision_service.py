import requests
from django.conf import settings


def process_images(image_paths: list[str]) -> dict:
    """
    Call the CNN model service to process grocery images and return an itemized bill.

    Args:
        image_paths: List of absolute file paths to uploaded images.
                     These are paths inside the shared Docker volume (/app/media/...).

    Returns:
        dict: {
            'remarks': str,            # overall remark from vision service
            'items': [                 # list of detected items
                {
                    'product_name': str,
                    'quantity': float,
                    'unit_price': float,
                    'remark': str      # per-item remark, may be empty
                },
                ...
            ]
        }

    Raises:
        requests.HTTPError: if the model service returns a non-2xx status
        requests.ConnectionError: if the model service is unreachable
        requests.Timeout: if the model service takes > 120s
    """
    response = requests.post(
        f"{settings.MODEL_SERVICE_URL}/predict",
        json={"image_paths": image_paths},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()
