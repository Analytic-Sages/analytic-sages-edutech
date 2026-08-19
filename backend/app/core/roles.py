from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    OPERATIONS = "operations"
    STUDENT = "student"
