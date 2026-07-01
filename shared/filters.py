from django.utils.dateparse import parse_datetime
from rest_framework.filters import BaseFilterBackend


class PostFilterBackend(BaseFilterBackend):
    """
    Custom filter backend for filtering posts by keyword search and date ranges.
    """

    def filter_queryset(self, request, queryset, view):
        search = request.query_params.get("search")
        date_from_str = request.query_params.get("date_from")
        date_to_str = request.query_params.get("date_to")

        if search:
            from django.db.models import Q

            queryset = queryset.filter(Q(title__icontains=search) | Q(content__icontains=search))

        if date_from_str:
            date_from = parse_datetime(date_from_str)
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)

        if date_to_str:
            date_to = parse_datetime(date_to_str)
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)

        return queryset

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": "search",
                "required": False,
                "in": "query",
                "description": "Keyword search term",
                "schema": {"type": "string"},
            },
            {
                "name": "date_from",
                "required": False,
                "in": "query",
                "description": "ISO format start date",
                "schema": {"type": "string"},
            },
            {
                "name": "date_to",
                "required": False,
                "in": "query",
                "description": "ISO format end date",
                "schema": {"type": "string"},
            },
        ]
