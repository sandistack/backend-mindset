from django.apps import AppConfig


class ChannelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.channels'
    label = 'chat_channels'  # Avoid conflict with third-party 'channels'
    verbose_name = 'Chat Channels'
