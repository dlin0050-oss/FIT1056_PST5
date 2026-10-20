"""app/user.py: Music School Management System module."""
class User:
    """Base class representing a user."""
    def __init__(self, id, name):
        """Store the shared ID and name attributes."""
        self.id = id
        self.name = name
