from enum import Enum


class Role(str, Enum):
    owner = "owner"
    admin = "admin"
    cashier = "cashier"


ADMIN_ROLES = {Role.owner, Role.admin}





