from django.shortcuts import render, get_object_or_404,redirect
from .models import Post, Comment
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from django.contrib import messages
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count

def home(request):
    count=6
    posts = Post.published.order_by('-publish')[:count]
    featured_post = Post.published.all()[7]
    return render(request, 'blog/main.html', {'posts':posts,'featured_post':featured_post})

@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None

    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
        messages.success(request, "Your comment has been added", 'success')
        return redirect(post.get_absolute_url())
    return render(request, 'blog/post/comment.html', {'post':post, 'form':form, 'comment':comment})


def post_share(request, post_id):
    tagzzz = Tag.objects.all()
    # Retrieve post by id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    if request.method == 'POST':
        # Form was submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form fields passed validation
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " f"{post.title}" 
            message = f"Read {post.title} at {post_url}\n\n" f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'your_account@gmail.com', [cd['to']])
            sent = True          
            messages.success(request, "Email was successfully sent to {}".format(cd['to']), 'success')
            return redirect(post.get_absolute_url())
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'tagzzz':tagzzz})


def post_list(request, tag_slug=None):
    tagzzz = Tag.objects.all()
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
        messages.success(request, "All posts by tag: {}".format(tag), 'primary')
    # Pagination with 3 posts per page
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page')
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        # If page_number is not an integer deliver the first page
        posts = paginator.page(1)
    except EmptyPage:
        # If page_number is out of range deliver last page of results
        posts = paginator.page(paginator.num_pages)
    
    return render(request, 'blog/post/list.html', {'posts': posts, 'tag':tag, 'tagzzz':tagzzz})


def post_detail(request, year, month, day, post):
    tagzzz = Tag.objects.all()
    post = get_object_or_404(Post,
                            status=Post.Status.PUBLISHED,
                            slug=post,
                            publish__year=year,
                            publish__month=month,
                            publish__day=day)
    # List of active comments for this post
    comments = post.comments.filter(active=True)
    # Form for users to comment
    form = CommentForm()
    # List of similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]
    return render(request, 'blog/post/detail.html', {'post': post, 'comments':comments, 'form':form, 'similar_posts': similar_posts, 'tagzzz':tagzzz})