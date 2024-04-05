import self
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Post
from .forms import EmailPostForm
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 2
    template_name = 'blog/post/list.html'

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

def post_share(request, post_id):
    #извлечь пост по идентификатору id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)

    sent = False

    if request.method == 'POST':
        #форма была передана на обработку
        form = EmailPostForm(request.POST)
        if form.is_valid():
            #поля формы успешно прошли вализацию
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n {cd['name']}'s comments: {cd['comments']}"
            send_mail(subject, message, cd['email'], [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html',
                  {'sent': sent, 'post': post, 'form': form})
