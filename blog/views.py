from django.shortcuts import render, get_object_or_404
from .models import Post, Category

def post_list(request):
    posts = Post.objects.filter(status='published').order_by('-created_at')
    categories = Category.objects.all()
    
    # Simple logic for "Tech Hub" heading
    return render(request, 'blog/post_list.html', {
        'posts': posts,
        'categories': categories
    })

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status='published')
    related_posts = Post.objects.filter(status='published', category=post.category).exclude(id=post.id)[:3]
    
    return render(request, 'blog/post_detail.html', {
        'post': post,
        'related_posts': related_posts
    })
