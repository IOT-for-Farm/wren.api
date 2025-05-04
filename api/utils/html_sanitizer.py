import bleach
from bleach.css_sanitizer import CSSSanitizer
# from bleach.sanitizer import ALLOWED_TAGS, ALLOWED_ATTRIBUTES


# SAFE HTML TAGS FOR EMAIL TEMPLATES
SAFE_HTML_TAGS = [
    # Basic text formatting
    'p', 'br', 'span', 'div',
    
    # Text styling
    'b', 'strong', 'i', 'em', 'u', 's', 'strike',
    
    # Headers
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    
    # Lists
    'ul', 'ol', 'li',
    
    # Links (careful with these)
    'a',
    
    # Tables (common in email templates)
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    
    # Images (careful with these)
    'img',
    
    # Horizontal rule
    'hr',
    
    # Code/preformatted
    'pre', 'code',
    
    # Blockquote
    'blockquote',
    
    # Superscript/subscript
    'sup', 'sub',
    
    # Miscellaneous
    'html', 'body', 'head', 'meta', 'title',
    'style', 'section', 'article', 'aside', 'footer',
    'header', 'nav', 'main', 'figure', 'figcaption',
    'doctype'
]

# SAFE ATTRIBUTES PER TAG
SAFE_HTML_ATTRIBUTES = {
    # Global attributes (allowed on all tags)
    '*': ['style', 'class', 'id'],
    
    # Link-specific attributes
    'a': ['href', 'title', 'target', 'rel'],
    
    # Image-specific attributes
    'img': ['src', 'alt', 'width', 'height', 'style'],
    
    # Table-specific attributes
    'table': ['border', 'cellpadding', 'cellspacing', 'width', 'style'],
    'td': ['colspan', 'rowspan', 'width', 'height', 'style'],
    'th': ['colspan', 'rowspan', 'width', 'height', 'style'],
    
    # Style attributes for various elements
    'div': ['style'],
    'span': ['style'],
    'p': ['style']
}

# SAFE CSS PROPERTIES (for style attributes)
SAFE_CSS_PROPERTIES = [
    'color', 'background-color', 'font-family', 'font-size',
    'font-weight', 'font-style', 'text-decoration',
    'text-align', 'line-height', 'letter-spacing',
    'width', 'height', 'padding', 'padding-top',
    'padding-right', 'padding-bottom', 'padding-left',
    'margin', 'margin-top', 'margin-right', 'margin-bottom',
    'margin-left', 'border', 'border-top', 'border-right',
    'border-bottom', 'border-left', 'border-radius',
    'display', 'float', 'clear', 'vertical-align'
]

# PROTOCOLS ALLOWED IN LINKS AND IMAGES
SAFE_PROTOCOLS = ['http', 'https', 'mailto', 'tel']

# TAGS THAT SHOULD BE STRIPPED IF EMPTY
STRIP_EMPTY_TAGS = ['p', 'span', 'div']

# TAGS THAT SHOULD ALWAYS BE SANITIZED EVEN IF ALLOWED
FORCE_CLEAN_TAGS = ['a', 'img']


def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content for email templates with comprehensive protection.
    
    Args:
        html_content: Raw HTML input from untrusted source
        
    Returns:
        Sanitized HTML safe for email use
    """
    
    # Configure CSS sanitizer
    css_sanitizer = CSSSanitizer(allowed_css_properties=SAFE_CSS_PROPERTIES)
    
    # Perform sanitization
    clean_html = bleach.clean(
        html_content,
        tags=SAFE_HTML_TAGS,
        attributes=SAFE_HTML_ATTRIBUTES,
        css_sanitizer=css_sanitizer,
        protocols=SAFE_PROTOCOLS,
        strip=True,
        strip_comments=True
    )
    
    # Additional security for high-risk elements
    if any(tag in clean_html for tag in FORCE_CLEAN_TAGS):
        clean_html = bleach.clean(
            clean_html,
            tags=SAFE_HTML_TAGS,
            attributes=SAFE_HTML_ATTRIBUTES,
            protocols=SAFE_PROTOCOLS,
            strip=True
        )
    
    return clean_html
