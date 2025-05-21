from django import template
from django.template.defaultfilters import stringfilter
from django.template.loader import render_to_string

register = template.Library()

@register.filter
@stringfilter
def split(value, delimiter=','):
    """
    Bir stringi verilen ayırıcıya göre parçalar ve liste olarak döndürür.
    
    Kullanım:
    {{ "a,b,c"|split:"," }} -> ['a', 'b', 'c']
    """
    return value.split(delimiter)

@register.filter
def get_item(value, index):
    """
    Bir listeden belirtilen indeksteki öğeyi döndürür.
    
    Kullanım:
    {{ my_list|get_item:0 }} -> my_list'in ilk öğesi
    """
    try:
        return value[int(index)]
    except (IndexError, TypeError, ValueError):
        return ""

@register.filter
def get_attr(obj, attr):
    """
    Bir nesnenin belirtilen özelliğini döndürür. Eğer özellik bir fonksiyon ise,
    fonksiyonu parametresiz olarak çağırır ve sonucunu döndürür.
    
    Kullanım:
    {{ user|get_attr:"username" }} -> user.username
    {{ user|get_attr:"get_full_name" }} -> user.get_full_name()
    
    Ayrıca nokta notasyonu kullanılarak iç içe erişim desteklenir:
    {{ order|get_attr:"customer.name" }} -> order.customer.name
    """
    if '.' in attr:
        attrs = attr.split('.')
        value = obj
        for a in attrs:
            value = get_attr(value, a)
        return value
    
    try:
        value = getattr(obj, attr)
        if callable(value):
            return value()
        return value
    except (AttributeError, TypeError):
        try:
            return obj.get(attr)
        except (AttributeError, KeyError, TypeError):
            try:
                return obj[attr]
            except (KeyError, TypeError, IndexError):
                return ""

@register.simple_tag(takes_context=True)
def block_tag(context, blockname):
    """
    İsmi verilen bloğun içeriğini render eder.
    
    Kullanım:
    {% block_tag 'my_blockname' %}
    """
    try:
        block = context.template.engine.get_template(context.template.name).blocks[blockname]
        with context.push():
            return ''.join(block(context) or '')
    except (KeyError, AttributeError):
        return ""

@register.simple_tag(takes_context=True)
def component(context, component_name, **kwargs):
    """
    Verilen komponenti render eder.
    
    Kullanım:
    {% component 'card' title='Başlık' %}
    """
    # İçerik ekle
    content = kwargs.pop('content', None)
    
    # Bileşen şablonunu render et
    template_name = f'components/{component_name}.html'
    
    # Yeni context oluştur
    component_context = {
        'content': content,
        **kwargs
    }
    
    # User'ı context'e ekle (eğer varsa)
    if 'request' in context:
        component_context['request'] = context['request']
    if 'user' in context:
        component_context['user'] = context['user']
    
    from django.utils.safestring import mark_safe
    return mark_safe(render_to_string(template_name, component_context))

@register.simple_tag
def component_start(component_name, **kwargs):
    """
    Bir komponenti başlatır.
    
    Kullanım:
    {% component_start 'card' %}
        İçerik
    {% component_end %}
    """
    # Bileşen şablonunu render et (başlangıç kısmı)
    template_name = f'components/{component_name}_start.html'
    
    try:
        return render_to_string(template_name, kwargs)
    except:
        # Eğer _start şablonu yoksa, normal şablonu kullan
        template_name = f'components/{component_name}.html'
        return f'<div class="component-{component_name}">'

@register.simple_tag
def component_end():
    """
    Bir komponenti sonlandırır.
    """
    return '</div>'