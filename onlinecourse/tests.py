from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Course, Enrollment, Question, Choice, Submission

class AssessmentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('student', password='local-test-only')
        self.other = User.objects.create_user('other', password='local-test-only')
        self.course = Course.objects.create(name='Django', description='Test course')
        self.enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        self.question = Question.objects.create(course=self.course, content='Choose Python frameworks', grade=100)
        self.a = Choice.objects.create(question=self.question, content='Django', is_correct=True)
        self.b = Choice.objects.create(question=self.question, content='Flask', is_correct=True)
        self.c = Choice.objects.create(question=self.question, content='Express', is_correct=False)
        self.url = reverse('onlinecourse:submit', args=[self.course.id])
        self.client.force_login(self.user)

    def submit(self, ids):
        return self.client.post(self.url, {'choice': ids}, follow=True)

    def test_exact_multiple_selection_passes(self):
        response = self.submit([self.a.id, self.b.id])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Congratulations')
        self.assertEqual(response.context['grade'], 100)
        self.assertEqual(Submission.objects.get().choices.count(), 2)

    def test_extra_wrong_answer_fails(self):
        response = self.submit([self.a.id, self.b.id, self.c.id])
        self.assertEqual(response.context['grade'], 0)
        self.assertContains(response, 'Re-test')

    def test_partial_answer_fails(self):
        self.assertEqual(self.submit([self.a.id]).context['grade'], 0)

    def test_empty_answer_fails(self):
        self.assertEqual(self.submit([]).context['grade'], 0)

    def test_duplicate_choices_do_not_change_score(self):
        self.assertEqual(self.submit([self.a.id, self.a.id, self.b.id]).context['grade'], 100)

    def test_malformed_id_rejected_without_submission(self):
        self.assertEqual(self.client.post(self.url, {'choice': 'invalid'}).status_code, 400)
        self.assertFalse(Submission.objects.exists())

    def test_foreign_course_choice_rejected(self):
        foreign = Course.objects.create(name='Other')
        question = Question.objects.create(course=foreign, content='Other')
        choice = Choice.objects.create(question=question, content='Foreign')
        self.assertEqual(self.client.post(self.url, {'choice': choice.id}).status_code, 400)
        self.assertFalse(Submission.objects.exists())

    def test_get_submit_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_anonymous_must_log_in(self):
        self.client.logout()
        self.assertEqual(self.client.post(self.url).status_code, 302)

    def test_unenrolled_cannot_submit(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.url).status_code, 404)

    def test_another_student_cannot_view_result(self):
        self.submit([self.a.id, self.b.id])
        result = Submission.objects.get()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('onlinecourse:show_exam_result', args=[self.course.id, result.id])).status_code, 404)

    def test_retake_records_separate_submission(self):
        self.submit([self.c.id])
        self.submit([self.a.id, self.b.id])
        self.assertEqual(Submission.objects.count(), 2)

    def test_empty_exam_safe(self):
        self.question.delete()
        self.assertEqual(self.submit([]).context['grade'], 0)

    def test_course_template_has_csrf_questions_and_choices(self):
        response = self.client.get(reverse('onlinecourse:course_details', args=[self.course.id]))
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, 'Choose Python frameworks')
        self.assertContains(response, 'Start Exam')

    def test_admin_models_registered(self):
        from django.contrib import admin
        for model in (Question, Choice, Submission):
            self.assertIn(model, admin.site._registry)

    def test_unenrolled_detail_offers_enrollment(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('onlinecourse:course_details', args=[self.course.id]))
        self.assertNotContains(response, 'Start Exam')
        self.assertContains(response, 'Enroll in this course')

    def test_enrollment_requires_post(self):
        self.assertEqual(self.client.get(reverse('onlinecourse:enroll', args=[self.course.id])).status_code, 405)

    def test_repeated_enrollment_is_idempotent(self):
        self.client.force_login(self.other)
        url = reverse('onlinecourse:enroll', args=[self.course.id])
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(Enrollment.objects.filter(user=self.other, course=self.course).count(), 1)

    def test_registration_rejects_missing_and_weak_passwords(self):
        self.client.logout()
        url = reverse('onlinecourse:registration')
        for data in ({}, {'username': 'weak', 'psw': '1'}):
            self.assertEqual(self.client.post(url, data).status_code, 200)
        self.assertFalse(User.objects.filter(username='weak').exists())

    def test_login_with_missing_fields_does_not_error(self):
        self.client.logout()
        self.assertEqual(self.client.post(reverse('onlinecourse:login'), {}).status_code, 200)
