import logging

logger = logging.getLogger(__name__)

def log_page_view(page_name: str) -> None:
    """
    Log when a page is viewed.
    
    Args:
        page_name: The name of the page being viewed
    """
    logger.debug(f"Rendering {page_name} page") 