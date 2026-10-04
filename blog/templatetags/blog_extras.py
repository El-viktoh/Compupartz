import html
import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='render_markdown')
def render_markdown(text):
    """
    Safely renders markdown formatting (headings, lists, bold, italics, paragraphs)
    into styled HTML tailored for Compupartz tech briefings.
    """
    if not text:
        return ''

    escaped = html.escape(str(text))
    lines = escaped.splitlines()

    output = []
    current_list_type = None  # 'ul' or 'ol'
    list_items = []
    paragraph_lines = []

    def flush_list():
        nonlocal current_list_type, list_items
        if current_list_type and list_items:
            tag = current_list_type
            cls = 'list-disc' if tag == 'ul' else 'list-decimal'
            items_html = ''.join(f'<li>{item}</li>' for item in list_items)
            output.append(f'<{tag} class="{cls} pl-6 my-4 space-y-2 text-slate-700 dark:text-gray-300 leading-relaxed font-light">{items_html}</{tag}>')
            current_list_type = None
            list_items = []

    def flush_paragraph():
        nonlocal paragraph_lines
        if paragraph_lines:
            p_text = '<br>'.join(paragraph_lines)
            p_text = re.sub(r'\*\*(.*?)\*\*', r'<strong class="font-semibold text-slate-900 dark:text-white">\1</strong>', p_text)
            p_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', p_text)
            output.append(f'<p class="mb-4 leading-relaxed text-slate-700 dark:text-gray-300 font-light">{p_text}</p>')
            paragraph_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        if stripped.startswith('### '):
            flush_paragraph()
            flush_list()
            h_text = stripped[4:].strip()
            h_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', h_text)
            output.append(f'<h3 class="text-lg sm:text-xl font-bold text-slate-900 dark:text-white mt-8 mb-3 font-display">{h_text}</h3>')
        elif stripped.startswith('## '):
            flush_paragraph()
            flush_list()
            h_text = stripped[3:].strip()
            h_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', h_text)
            output.append(f'<h2 class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white mt-9 mb-4 font-display">{h_text}</h2>')
        elif re.match(r'^[0-9]+\.\s', stripped):
            flush_paragraph()
            if current_list_type != 'ol':
                flush_list()
                current_list_type = 'ol'
            item_text = re.sub(r'^[0-9]+\.\s*', '', stripped)
            item_text = re.sub(r'\*\*(.*?)\*\*', r'<strong class="font-semibold text-slate-900 dark:text-white">\1</strong>', item_text)
            list_items.append(item_text)
        elif stripped.startswith('- ') or stripped.startswith('* '):
            flush_paragraph()
            if current_list_type != 'ul':
                flush_list()
                current_list_type = 'ul'
            item_text = stripped[2:].strip()
            item_text = re.sub(r'\*\*(.*?)\*\*', r'<strong class="font-semibold text-slate-900 dark:text-white">\1</strong>', item_text)
            list_items.append(item_text)
        else:
            flush_list()
            paragraph_lines.append(stripped)

    flush_paragraph()
    flush_list()
    return mark_safe('\n'.join(output))
