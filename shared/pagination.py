from rest_framework.pagination import LimitOffsetPagination


class PostLimitOffsetPagination(LimitOffsetPagination):
    """
    Standard limit offset pagination for posts.
    """

    default_limit = 10
    max_limit = 100
