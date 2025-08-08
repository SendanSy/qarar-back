"""
Custom pagination classes for the Qarar platform
"""
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination with configurable page size
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_page_size(self, request):
        """
        Determine the page size for the request
        """
        if self.page_size_query_param:
            try:
                page_size = int(request.query_params.get(self.page_size_query_param, self.page_size))
                if page_size > 0:
                    if self.max_page_size:
                        return min(page_size, self.max_page_size)
                    return page_size
            except (ValueError, TypeError):
                pass
        return self.page_size