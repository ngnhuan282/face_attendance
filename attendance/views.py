import json

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.constants import ADMIN_GROUP_NAME, TEACHER_GROUP_NAME
from accounts.permissions import group_required
from courses.models import CourseClass, Enrollment
from recognition.face_matcher import recognize_from_image
from schedules.models import Schedule
from students.models import Student

from .models import AttendanceRecord, AttendanceSession


def _json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"JSON khong hop le: {exc}")


def _ok(data=None, status=200):
    return JsonResponse(data or {}, status=status, json_dumps_params={"ensure_ascii": False})


def _error(message, status=400):
    return _ok({"error": message}, status=status)


def _session_payload(session):
    return {
        "id": session.id,
        "course_class_id": session.course_class_id,
        "course_class": session.course_class.class_code,
        "schedule_id": session.schedule_id,
        "created_by_id": session.created_by_id,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "status": session.status,
        "note": session.note,
    }


def _record_payload(record):
    return {
        "id": record.id,
        "session_id": record.session_id,
        "student_id": record.student_id,
        "student_code": record.student.student_id,
        "student_name": record.student.full_name,
        "status": record.status,
        "method": record.method,
        "confidence": record.confidence,
        "timestamp": record.timestamp.isoformat() if record.timestamp else None,
        "note": record.note,
    }


def _default_user(request):
    if request.user.is_authenticated:
        return request.user
    return User.objects.order_by("id").first()


@group_required(ADMIN_GROUP_NAME, TEACHER_GROUP_NAME)
def attendance_demo(request):
    course_classes = CourseClass.objects.select_related("course", "semester", "teacher").order_by(
        "semester", "class_code"
    )
    selected_session = None
    students = []
    records_by_student = {}
    student_rows = []
    error_message = ""

    if request.method == "POST":
        course_class_id = request.POST.get("course_class_id")
        note = request.POST.get("note", "")

        try:
            course_class = get_object_or_404(CourseClass, pk=course_class_id)
            selected_session = AttendanceSession.objects.create(
                course_class=course_class,
                created_by=request.user,
                note=note,
            )
            return redirect(f"{reverse('attendance:demo')}?session_id={selected_session.id}")
        except (ValidationError, IntegrityError) as exc:
            error_message = str(exc)

    session_id = request.GET.get("session_id")
    if session_id:
        selected_session = get_object_or_404(
            AttendanceSession.objects.select_related("course_class", "course_class__course", "created_by"),
            pk=session_id,
        )
        students = [
            enrollment.student
            for enrollment in Enrollment.objects.select_related("student", "student__student_class")
            .filter(course_class=selected_session.course_class, is_active=True)
            .order_by("student__student_id")
        ]
        records_by_student = {
            record.student_id: record
            for record in AttendanceRecord.objects.filter(session=selected_session).select_related("student")
        }
        student_rows = [
            {
                "student": student,
                "record": records_by_student.get(student.id),
            }
            for student in students
        ]

    return render(
        request,
        "attendance/create_session.html",
        {
            "active_menu": "attendance",
            "course_classes": course_classes,
            "selected_session": selected_session,
            "session_id_json": selected_session.id if selected_session else None,
            "students": students,
            "student_rows": student_rows,
            "error_message": error_message,
        },
    )


@csrf_exempt
@require_http_methods(["GET", "POST"])
def session_list_create(request):
    if request.method == "GET":
        sessions = AttendanceSession.objects.select_related("course_class", "schedule", "created_by")
        return _ok({"results": [_session_payload(session) for session in sessions]})

    try:
        data = _json_body(request)
        user = _default_user(request)
        if not user:
            return _error("Can co it nhat 1 User de gan created_by.", status=400)

        course_class = get_object_or_404(CourseClass, pk=data.get("course_class_id"))
        schedule = None
        if data.get("schedule_id"):
            schedule = get_object_or_404(Schedule, pk=data["schedule_id"])

        session = AttendanceSession.objects.create(
            course_class=course_class,
            schedule=schedule,
            created_by=user,
            status=data.get("status", "open"),
            note=data.get("note", ""),
        )
        return _ok(_session_payload(session), status=201)
    except (ValidationError, IntegrityError) as exc:
        return _error(str(exc), status=400)


@csrf_exempt
@require_http_methods(["GET", "PATCH", "PUT", "DELETE"])
def session_detail(request, pk):
    session = get_object_or_404(
        AttendanceSession.objects.select_related("course_class", "schedule", "created_by"),
        pk=pk,
    )

    if request.method == "GET":
        return _ok(_session_payload(session))

    if request.method == "DELETE":
        session.delete()
        return _ok({"deleted": True})

    try:
        data = _json_body(request)
        if "course_class_id" in data:
            session.course_class = get_object_or_404(CourseClass, pk=data["course_class_id"])
        if "schedule_id" in data:
            session.schedule = get_object_or_404(Schedule, pk=data["schedule_id"]) if data["schedule_id"] else None
        if "status" in data:
            session.status = data["status"]
            if data["status"] == "closed" and not session.ended_at:
                session.ended_at = timezone.now()
        if "note" in data:
            session.note = data["note"]
        session.full_clean()
        session.save()
        return _ok(_session_payload(session))
    except (ValidationError, IntegrityError) as exc:
        return _error(str(exc), status=400)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def record_list_create(request):
    if request.method == "GET":
        records = AttendanceRecord.objects.select_related("session", "student")
        session_id = request.GET.get("session_id")
        if session_id:
            records = records.filter(session_id=session_id)
        return _ok({"results": [_record_payload(record) for record in records]})

    try:
        data = _json_body(request)
        session = get_object_or_404(AttendanceSession, pk=data.get("session_id"))
        student = get_object_or_404(Student, pk=data.get("student_id"))
        record = AttendanceRecord.objects.create(
            session=session,
            student=student,
            status=data.get("status", "present"),
            method=data.get("method", "manual"),
            confidence=float(data.get("confidence", 0.0)),
            timestamp=timezone.now(),
            note=data.get("note", ""),
        )
        return _ok(_record_payload(record), status=201)
    except (ValidationError, IntegrityError, ValueError) as exc:
        return _error(str(exc), status=400)


@csrf_exempt
@require_http_methods(["GET", "PATCH", "PUT", "DELETE"])
def record_detail(request, pk):
    record = get_object_or_404(AttendanceRecord.objects.select_related("session", "student"), pk=pk)

    if request.method == "GET":
        return _ok(_record_payload(record))

    if request.method == "DELETE":
        record.delete()
        return _ok({"deleted": True})

    try:
        data = _json_body(request)
        if "session_id" in data:
            record.session = get_object_or_404(AttendanceSession, pk=data["session_id"])
        if "student_id" in data:
            record.student = get_object_or_404(Student, pk=data["student_id"])
        for field in ["status", "method", "confidence", "note"]:
            if field in data:
                setattr(record, field, data[field])
        if "timestamp" not in data:
            record.timestamp = timezone.now()
        record.full_clean()
        record.save()
        return _ok(_record_payload(record))
    except (ValidationError, IntegrityError, ValueError) as exc:
        return _error(str(exc), status=400)


@csrf_exempt
@require_http_methods(["POST"])
def recognize_attendance(request):
    session_id = request.POST.get("session_id")
    image_file = request.FILES.get("image")

    if not session_id:
        return _error("Thieu session_id.", status=400)
    if not image_file:
        return _error("Thieu file anh voi field name la image.", status=400)

    session = get_object_or_404(AttendanceSession, pk=session_id)

    try:
        result = recognize_from_image(image_file)
    except Exception as exc:
        return _error(f"Loi nhan dien khuon mat: {exc}", status=400)

    if not result:
        return _error("Khong nhan dien duoc sinh vien trong anh.", status=404)

    student = get_object_or_404(Student, student_id=result["student_id"])
    is_enrolled = Enrollment.objects.filter(
        course_class=session.course_class,
        student=student,
        is_active=True,
    ).exists()
    if not is_enrolled:
        return _error("Sinh vien nhan dien duoc khong thuoc lop hoc phan nay.", status=400)

    record, created = AttendanceRecord.objects.update_or_create(
        session=session,
        student=student,
        defaults={
            "status": "present",
            "method": "face",
            "confidence": result["confidence"],
            "timestamp": timezone.now(),
            "note": "Auto recognized by face_matcher",
        },
    )

    return _ok(
        {
            "created": created,
            "match": result,
            "record": _record_payload(record),
        },
        status=201 if created else 200,
    )
