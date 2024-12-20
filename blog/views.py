from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from taggit.models import Tag

from .models import Post, Comment
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank


# def post_list(request):
#     post_list = Post.published.all()
#     #постраничная разбивка с 3 постами на страницу
#     paginator = Paginator(post_list, 3)
#     #параметр page содержит номер запрошенной страницы, если нет page, то возвращаем 1-ю страницу
#     page_number = request.GET.get('page', 1)
#     try:
#         posts = paginator.page(page_number)
#     except PageNotAnInteger:
#         #если страница не целое число, то выдаем 1 стр
#         posts = paginator.page(1)
#     except EmptyPage:
#         #если номер страницы нах-ся вне диапозона, то выдаем посл стр
#         posts = paginator.page(paginator.num_pages)
#     return render(request, 'blog/post/list.html', {'posts': posts})

class PostListView(ListView):
    context_object_name = 'posts'
    paginate_by = 2
    template_name = 'blog/post/list.html'

    def get_queryset(self):
        queryset = Post.published.all()
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            queryset = queryset.filter(tags__in=[tag])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            context["search_by_tag"] = tag
        return context



# def post_detail(request, year, month, day, post):
#     post = get_object_or_404(Post,
#                              status=Post.Status.PUBLISHED,
#                              slug=post,
#                              publish__year=year,
#                              publish__month=month,
#                              publish__day=day)
#     return render(request, 'blog/post/detail.html', {'post': post})

class PostDetailView(DetailView):
    model = Post
    context_object_name = 'post'
    template_name = 'blog/post/detail.html'

    def get_object(self, queryset=None):
        year = self.kwargs.get('year')
        month = self.kwargs.get('month')
        day = self.kwargs.get('day')
        slug = self.kwargs.get('post')
        post = get_object_or_404(Post, publish__year=year,
                                 publish__month=month, publish__day=day, slug=slug)
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object

        comments = post.comments.filter(active=True)
        context['comments'] = comments

        form = CommentForm()
        context['form'] = form

        # post_tags_ids = post.tags.values_list('id', flat=True)
        # similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
        # similar_posts = similar_posts.annotate(same_tags=Count('tags',
        #                                     filter=Q(tags__in=post_tags_ids))).order_by('-same_tags', '-publish')[:4]

        similar_posts = post.tags.similar_objects()[::-1][:4]
        context['similar_posts'] = similar_posts

        return context


def post_share(request, post_id):
    #извлечь пост по идентификатору id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)

    sent = False

    if request.method == 'POST':
        #форма была передана на обработку
        form = EmailPostForm(request.POST)
        if form.is_valid():
            #поля формы успешно прошли валидацию
            cd = form.cleaned_data
            post_url = request.build_absolute_url(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n {cd['name']}'s comments: {cd['comments']}"
            send_mail(subject, message, cd['email'], [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html',
                  {'sent': sent, 'post': post, 'form': form})

@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    #Комментарий был отправлен
    form = CommentForm(request.POST)
    if form.is_valid():
        #Создать объект класса Comment, не сохраняя его в базе данных
        comment = form.save(commit=False)
        #Назначить пост комментарию
        comment.post = post
        #Сохранить комментарий в базе данных
        comment.save()
    return render(request, 'blog/post/comment.html',
                  {'post': post, 'form': form, 'comment': comment})

def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A') + \
                            SearchVector('body', weight='B')
            search_query = SearchQuery(query)
            results = (Post.published.annotate(
                # search=search_vector,
                rank=SearchRank(search_vector, search_query),
                ).filter(rank__gte=0.1)).order_by('-rank')

    return render(request, 'blog/post/search.html',
                  {'form': form, 'query': query, 'results': results})



