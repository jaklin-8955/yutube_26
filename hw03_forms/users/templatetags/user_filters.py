from django import template

register = template.Library()

@register.filter(name='addclass')
def addclass(value, arg):
    """Добавляет CSS-класс к полю формы."""
    return value.as_widget(attrs={'class': arg})