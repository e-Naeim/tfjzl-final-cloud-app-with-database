from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    from django.contrib.auth.forms import UserCreationForm
    context = {}
    if request.method == 'POST':
        form = UserCreationForm({
            'username': request.POST.get('username', ''),
            'password1': request.POST.get('psw', ''),
            'password2': request.POST.get('psw', ''),
        })
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = request.POST.get('firstname', '')[:150]
            user.last_name = request.POST.get('lastname', '')[:150]
            user.save()
            login(request, user)
            return redirect('onlinecourse:index')
        context['message'] = ' '.join(error for errors in form.errors.values() for error in errors)
    return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST.get('username', '')
        password = request.POST.get('psw', '')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_enrolled'] = check_if_enrolled(self.request.user, self.object)
        return context


@login_required
@require_POST
@transaction.atomic
def enroll(request, course_id):
    from django.db.models import F
    course = get_object_or_404(Course, pk=course_id)
    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user, course=course, defaults={'mode': 'honor'})
    if created:
        Course.objects.filter(pk=course.id).update(total_enrollment=F('total_enrollment') + 1)
    return redirect('onlinecourse:course_details', course.id)


def extract_answers(request):
    answers = set()
    for key in request.POST:
        if key.startswith('choice'):
            for value in request.POST.getlist(key):
                answers.add(int(value))
    return answers


@login_required
@require_POST
@transaction.atomic
def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    try:
        selected_ids = extract_answers(request)
    except (ValueError, TypeError):
        return HttpResponseBadRequest('Invalid choice identifier.')
    choices = Choice.objects.filter(question__course=course, id__in=selected_ids)
    if choices.count() != len(selected_ids):
        return HttpResponseBadRequest('A choice does not belong to this course.')
    submission = Submission.objects.create(enrollment=enrollment)
    submission.choices.set(choices)
    return redirect('onlinecourse:show_exam_result', course_id, submission.id)


@login_required
def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(
        Submission, pk=submission_id,
        enrollment__course=course, enrollment__user=request.user)
    selected_ids = set(submission.choices.values_list('id', flat=True))
    results, earned, possible = [], 0, 0
    for question in course.question_set.prefetch_related('choice_set').all():
        correct = question.is_get_score(selected_ids)
        earned += question.grade if correct else 0
        possible += question.grade
        results.append({'question': question, 'correct': correct,
                        'choices': question.choice_set.all()})
    grade = round(100 * earned / possible, 2) if possible else 0
    return render(request, 'onlinecourse/exam_result_bootstrap.html', {
        'course': course, 'submission': submission, 'grade': grade,
        'earned': earned, 'possible': possible, 'passed': grade > 80,
        'selected_ids': selected_ids, 'results': results})
