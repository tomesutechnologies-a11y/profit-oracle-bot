from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .models import Post
from .forms import PostForm, CommentForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponseBadRequest
from django.template.loader import render_to_string

# Create your views here.
def home(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def gallery(request):
    return render(request, 'gallery.html'  )
def contact(request):
    return render(request, 'contact.html')

def videos(request):
    return render(request, 'videos.html')

def blog(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 6)  # Show 6 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog.html', {'posts': page_obj.object_list, 'page_obj': page_obj, 'paginator': paginator})
    return render(request, 'blog.html')

def blog_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    comments = post.comments.all()
    new_comment = None

    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()
            return redirect('blog_detail', slug=post.slug)
    else:
        comment_form = CommentForm()

    return render(request, 'blog_detail.html', {'post': post, 'comments': comments, 'new_comment': new_comment, 'comment_form': comment_form})


def sitemap(request):
    posts = Post.objects.all().order_by('-created_at')
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    # Static pages
    static_views = [
        ('home', None),
        ('about', None),
        ('gallery', None),
        ('videos', None),
        ('contact', None),
        ('blog', None),
        
    ]
    for name, args in static_views:
        url = request.build_absolute_uri(reverse(name))
        xml += f'<url><loc>{url}</loc></url>\n'
    # Blog posts
    for post in posts:
        post_url = request.build_absolute_uri(reverse('post_detail', args=[post.slug]))
        xml += f'<url><loc>{post_url}</loc><lastmod>{post.updated_at.date()}</lastmod></url>\n'
    xml += '</urlset>'
    return HttpResponse(xml, content_type='application/xml')