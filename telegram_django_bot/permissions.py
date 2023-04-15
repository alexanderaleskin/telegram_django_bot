

class BasePermissionClass:
    def has_permissions(self, bot, update, user, utrl_args, **kwargs):
        raise NotImplementedError()


class PermissionAllowAny(BasePermissionClass):
    def has_permissions(self, bot, update, user, utrl_args, **kwargs):
        return True


