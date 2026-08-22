from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    AUTHOR = "author"
    INSTRUCTOR = "instructor"
    OPERATIONS = "operations"
    STUDENT = "student"
