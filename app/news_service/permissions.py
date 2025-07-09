from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthenticatedReadOnlyOrAdmin(BasePermission):
    """
    Custom permission to only allow authenticated users to read,
    and admin users to perform any action.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False

        # Allow read-only methods (GET, HEAD, OPTIONS) for authenticated users
        if request.method in SAFE_METHODS:
            return True

        # Only allow write methods for admin users
        return request.user.is_staff