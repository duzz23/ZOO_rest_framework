import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView

from ai_agent.api import ask_ai
from ai_agent.prompts import create_llm, create_question_rewrite_chain
from ai_agent.embeddings import create_embeddings
from ai_agent.chains import create_rag_chain
from ai_agent.retriever import RetrieverManager

from .models import Category, Animal
from .forms import AnimalForm, ContactForm


def index_view(request):
    return render(request, 'mainapp/index.html' , context={'title': 'Главная страница'})


def category_list_view(request):
    category_list = Category.objects.all()
    context = {'category_list': category_list}
    return render(request, 'mainapp/category_list.html', context=context)


class CategoryListView(ListView):
    model = Category
    ordering = ['pk']
    # template_name = ''
    # context_object_name =

    # get - гет запрос
    # get_context_data - передача контектса в шаблон
    # get_queryset - получение данных

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['some_text'] = 'Another text'
        return context



class CategoryDetailView(DetailView):
    model = Category

    # get - гет запрос
    # get_context_data - передача контектса в шаблон
    # get_queryset - получение данных
    # get_object - получение одного объекта


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    fields = '__all__'
    success_url = reverse_lazy('mainapp:category_list')

    # get - гет запрос
    # get_context_data - передача контектса в шаблон
    # post
    # form_valid
    # get_success_url


class CategoryUpdateView(UpdateView):
    model = Category
    fields = '__all__'
    success_url = reverse_lazy('mainapp:category_list')

    # get - гет запрос
    # get_context_data - передача контектса в шаблон
    # post
    # form_valid
    # get_object
    # get_success_url

class CategoryDeleteView(DeleteView):
    model = Category
    success_url = reverse_lazy('mainapp:category_list')
    # get - гет запрос
    # get_context_data - передача контектса в шаблон
    # post
    # form_valid
    # get_object
    # get_success_url


class AnimalListView(ListView):
    model = Animal
    template_name = 'mainapp/animals.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['categories'] = Category.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        self.category_id = request.GET.get('category_id', None)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.category_id is not None:
            queryset = queryset.filter(category__id=self.category_id)

        queryset = queryset.select_related('category')
        queryset = queryset.prefetch_related('food')

        for animal in queryset:
            print(animal.show_food)
            print(animal.show_food)
            print(animal.show_food)
            print(animal.show_food)
            print(animal.show_food)
        return queryset


class AnimalCreateView(CreateView):
    model = Animal
    form_class = AnimalForm
    success_url = reverse_lazy('mainapp:animal_list')


class ContactFormView(FormView):
    form_class = ContactForm
    success_url = reverse_lazy('mainapp:index')
    template_name = 'mainapp/contact.html'

    def form_valid(self, form):
        data = form.cleaned_data
        print('MESSAGE', data['message'])
        return super().form_valid(form)


# Кэшированные зависимости для RAG
_llm = None
_embeddings = None
_rewrite_chain = None
_rag_chain = None
_retriever_manager = None


def _get_rag_dependencies():
    """Ленивая инициализация RAG-зависимостей."""
    global _llm, _embeddings, _rewrite_chain, _rag_chain, _retriever_manager

    if _llm is None:
        _llm = create_llm()
    if _embeddings is None:
        _embeddings = create_embeddings()
    if _rewrite_chain is None:
        _rewrite_chain = create_question_rewrite_chain(_llm)
    if _rag_chain is None:
        _rag_chain = create_rag_chain(_llm)
    if _retriever_manager is None:
        _retriever_manager = RetrieverManager(_embeddings)

    return _rewrite_chain, _retriever_manager, _rag_chain


@require_POST
def ai_chat_view(request):
    """AJAX endpoint for the AI chat. Expects JSON with 'question' key."""
    try:
        data = json.loads(request.body)
        question = data.get("question", "").strip()
        if not question:
            return JsonResponse({"error": "Question is required"}, status=400)

        rewrite_chain, retriever_manager, rag_chain = _get_rag_dependencies()
        answer = ask_ai(
            question=question,
            rewrite_chain=rewrite_chain,
            retriever_manager=retriever_manager,
            rag_chain=rag_chain,
        )
        return JsonResponse({"answer": answer})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
