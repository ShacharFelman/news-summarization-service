"""
Test cases for the users models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model


def create_user(email='user@example.com', password='testpass123', name='User Name'):
    """Create a sample user"""
    return get_user_model().objects.create_user(email=email, password=password, name=name)


class UserModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful"""
        email = "test@example.com"
        password = "Testpass123"
        name = "Test User"
        user = create_user(email=email, password=password, name=name)

        self.assertEqual(user.email, email.lower())
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.name, name)

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users"""
        sample_emails = [
            ["test1@EXAMPLE.com", 'test1@example.com'],
            ["Test2@Example.com", 'Test2@example.com'],
            ["TEST3@EXAMPLE.com", 'TEST3@example.com']
        ]

        for email, expected in sample_emails:
            user = create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_invalid_email(self):
        """Test creating a user with no email raises a ValueError"""
        with self.assertRaises(ValueError):
            create_user(email=None, password="test123", name="Test User")

    def test_create_new_superuser(self):
        """Test creating a new superuser"""
        email = "super@example.com"
        password = "Superpass123"
        name = "Super User"
        user = get_user_model().objects.create_superuser(email=email, password=password)

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
