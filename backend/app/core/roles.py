from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    AUTHOR = "author"
    INSTRUCTOR = "instructor"
    OPERATIONS = "operations"
    PARTNERSHIPS = "partnerships"
    STUDENT = "student"
