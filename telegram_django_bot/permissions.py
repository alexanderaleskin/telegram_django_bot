

class BasePermissionClass:
    def has_permissions(self, bot, update, user, utrl_args, **kwargs):
        raise NotImplementedError()


class AllowAny(BasePermissionClass):
    def has_permissions(self, *args, **kwargs):
        return True

