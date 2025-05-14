"""
Template tags for caching in VivaCRM v2.
"""
import time
import hashlib
from django import template
from django.core.cache import cache
from django.utils.html import mark_safe
from django.conf import settings
from django.utils.safestring import SafeString

register = template.Library()


@register.simple_tag(takes_context=True)
def cache_fragment(context, fragment_name, timeout=3600):
    """
    Cache a template fragment for a specified amount of time.
    
    Example usage:
    {% cache_fragment "homepage_products" 3600 %}
        <!-- Expensive template content here -->
    {% endcache_fragment %}
    
    Args:
        context: The template context
        fragment_name: The name of the fragment to cache
        timeout: Cache timeout in seconds (default: 1 hour)
        
    Returns:
        str: A unique ID to identify this fragment in the template
    """
    # Create a unique ID for this fragment
    fragment_id = hashlib.md5(fragment_name.encode()).hexdigest()
    
    # Store the fragment details for the endcache_fragment tag
    if 'cached_fragments' not in context.render_context:
        context.render_context['cached_fragments'] = {}
    
    context.render_context['cached_fragments'][fragment_id] = {
        'name': fragment_name,
        'timeout': timeout
    }
    
    return fragment_id


@register.simple_tag(takes_context=True)
def endcache_fragment(context, fragment_id):
    """
    End a cacheable template fragment and return its content.
    
    Example usage:
    {% cache_fragment "homepage_products" 3600 as fragment_id %}
        <!-- Expensive template content here -->
    {% endcache_fragment fragment_id %}
    
    Args:
        context: The template context
        fragment_id: The fragment ID returned by cache_fragment
        
    Returns:
        str: The cached or newly rendered content
    """
    # Get the fragment details
    fragment_details = context.render_context.get('cached_fragments', {}).get(fragment_id)
    if not fragment_details:
        return ''
    
    # Extract the content between the tags
    content = context.render_context.get(f'fragment_content_{fragment_id}', '')
    
    # Generate a cache key
    user_id = getattr(context.get('request', {}).user, 'id', 'anonymous')
    fragment_name = fragment_details['name']
    cache_key = f"template_fragment:{fragment_name}:{user_id}"
    
    # Try to get from cache
    cached_content = cache.get(cache_key)
    if cached_content is not None:
        return mark_safe(cached_content)
    
    # Cache the content
    timeout = fragment_details['timeout']
    cache.set(cache_key, content, timeout)
    
    return mark_safe(content)


@register.tag
def cached(parser, token):
    """
    Cache the contents of a template fragment for a specified amount of time.
    
    Example usage:
    {% cached 3600 "sidebar" %}
        <!-- Expensive template content here -->
    {% endcached %}
    
    Args:
        parser: The template parser
        token: The template token
        
    Returns:
        CachedNode: A node that handles the caching
    """
    # Parse the tag arguments
    bits = token.split_contents()
    if len(bits) < 3:
        raise template.TemplateSyntaxError(
            f"'{bits[0]}' tag requires at least 2 arguments: "
            "the cache timeout and a fragment name."
        )
    
    timeout = bits[1]
    fragment_name = bits[2].strip('"\'')
    
    # Get the nodelist between the tags
    nodelist = parser.parse(('endcached',))
    parser.delete_first_token()  # Remove the 'endcached' token
    
    return CachedNode(nodelist, timeout, fragment_name)


class CachedNode(template.Node):
    """
    Node for the 'cached' template tag.
    """
    def __init__(self, nodelist, timeout, fragment_name):
        self.nodelist = nodelist
        self.timeout = template.Variable(timeout)
        self.fragment_name = fragment_name
    
    def render(self, context):
        # Resolve the timeout variable
        try:
            timeout = self.timeout.resolve(context)
        except template.VariableDoesNotExist:
            timeout = 3600  # Default to 1 hour
        
        # Generate a cache key
        user_id = getattr(context.get('request', {}).user, 'id', 'anonymous')
        cache_key = f"template_fragment:{self.fragment_name}:{user_id}"
        
        # Try to get from cache
        cached_content = cache.get(cache_key)
        if cached_content is not None:
            return cached_content
        
        # Render the content
        content = self.nodelist.render(context)
        
        # Cache the content
        cache.set(cache_key, content, timeout)
        
        return content


@register.simple_tag
def cached_include(template_name, timeout=3600, **kwargs):
    """
    Include and cache a template for a specified amount of time.
    
    Example usage:
    {% cached_include "includes/sidebar.html" 3600 %}
    
    Args:
        template_name: The name of the template to include
        timeout: Cache timeout in seconds (default: 1 hour)
        **kwargs: Additional context variables to pass to the template
        
    Returns:
        str: The rendered template
    """
    # Generate a cache key
    cache_key = f"template_include:{template_name}"
    
    # Add kwargs to cache key if provided
    if kwargs:
        kwargs_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        cache_key = f"{cache_key}:{kwargs_str}"
    
    # Try to get from cache
    cached_content = cache.get(cache_key)
    if cached_content is not None:
        return mark_safe(cached_content)
    
    # Render the template
    included_template = template.loader.get_template(template_name)
    content = included_template.render(kwargs)
    
    # Cache the content
    cache.set(cache_key, content, timeout)
    
    return mark_safe(content)


@register.simple_tag
def cache_time(timeout=0):
    """
    Return the current time, for use with cache invalidation.
    
    Example usage:
    <link rel="stylesheet" href="/static/css/style.css?v={% cache_time 3600 %}">
    
    Args:
        timeout: How frequently to update the timestamp, in seconds
        
    Returns:
        int: The current time, rounded to timeout intervals
    """
    if timeout > 0:
        # Round the current time to the nearest timeout interval
        return int(time.time() / timeout) * timeout
    else:
        # No caching, return current time
        return int(time.time())