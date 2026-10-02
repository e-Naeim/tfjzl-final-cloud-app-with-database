from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from onlinecourse.models import Course, Instructor, Lesson, Question, Choice, Enrollment

class Command(BaseCommand):
    help = 'Create course demonstration data; set the admin password interactively with changepassword.'
    def handle(self, *args, **options):
        admin, created = User.objects.get_or_create(username='admin', defaults={'is_staff': True, 'is_superuser': True, 'first_name': 'Emad'})
        if created:
            admin.set_unusable_password()
            admin.save()
        instructor, _ = Instructor.objects.get_or_create(user=admin, defaults={'full_time': True, 'total_learners': 1})
        course, _ = Course.objects.get_or_create(name='Learning Django', defaults={'description': 'Django is an extremely popular and fully featured server-side web framework, written in Python', 'pub_date': date.today(), 'image': 'course_images/question.png', 'total_enrollment': 1})
        course.instructors.add(instructor)
        Lesson.objects.get_or_create(course=course, title='What is Django', defaults={'order': 0, 'content': 'Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. It is free and open source.'})
        question, _ = Question.objects.get_or_create(course=course, content='Is Django a Python framework', defaults={'grade': 100})
        Choice.objects.get_or_create(question=question, content='Yes', defaults={'is_correct': True})
        Choice.objects.get_or_create(question=question, content='No', defaults={'is_correct': False})
        Enrollment.objects.get_or_create(user=admin, course=course, defaults={'mode':'honor'})
        self.stdout.write(self.style.SUCCESS(f'Demo course ready: /onlinecourse/{course.id}/'))
