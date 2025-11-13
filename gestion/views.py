from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from django.db.models import CharField
from django.contrib.postgres.lookups import Unaccent
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from datetime import datetime
import calendar
import os, csv

from asm.decorators import group_required
from asm.commons import get_float, get_int, get_or_none, get_param, get_session, set_session, show_exc, generate_qr, csv_export
from .models import Employee, Client, Assistance, ClientTimetable, Zone, Incident

CharField.register_lookup(Unaccent)
ACCESS_PATH="{}/gestion/assistances/client/".format(settings.MAIN_URL)


def init_session_date(request, key):
    #if not key in request.session:
    set_session(request, key, datetime.now().strftime("%Y-%m-%d"))

def get_assistances(request):
    value = get_session(request, "s_name")
    i_date = datetime.strptime("{} 00:00".format(get_session(request, "s_idate")), "%Y-%m-%d %H:%M")
    e_date = datetime.strptime("{} 23:59".format(get_session(request, "s_edate")), "%Y-%m-%d %H:%M")

    kwargs = {"ini_date__gte": i_date, "ini_date__lte": e_date}
    if value != "":
        kwargs["employee__name__unaccent__icontains"] = value

    return Assistance.objects.filter(**kwargs).order_by("-ini_date")

@group_required("Administradores",)
def index(request):
    init_session_date(request, "s_idate")
    init_session_date(request, "s_edate")
    return render(request, "index.html", {"item_list": get_assistances(request)})

@group_required("Administradores",)
def assistances_list(request):
    return render(request, "assistances-list.html", {"item_list": get_assistances(request)})

@group_required("Administradores",)
def assistances_search(request):
    set_session(request, "s_name", get_param(request.GET, "s_name"))
    set_session(request, "s_idate", get_param(request.GET, "s_idate"))
    set_session(request, "s_edate", get_param(request.GET, "s_edate"))
    return render(request, "assistances-list.html", {"item_list": get_assistances(request)})

@group_required("Administradores",)
def assistances_form(request):
    obj = get_or_none(Assistance, get_param(request.GET, "obj_id"))
    context = {'obj': obj, 'client_list': Client.objects.all(), 'emp_list': Employee.objects.all()}
    return render(request, "assistances-form.html", context)

@group_required("Administradores",)
def assistances_form_save(request):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    obj = get_or_none(Assistance, get_param(request.GET, "obj_id"))
    if obj == None:
        obj = Assistance.objects.create()
    obj.client = get_or_none(Client, get_param(request.GET, "client"))
    obj.employee = get_or_none(Employee, get_param(request.GET, "employee"))
    ini_date = get_param(request.GET, "ini_date")
    end_date = get_param(request.GET, "end_date")
    ini_time = get_param(request.GET, "ini_time")
    end_time = get_param(request.GET, "end_time")
    finish = get_param(request.GET, "finish")
    idate = datetime.strptime("{} {}".format(ini_date, ini_time), "%Y-%m-%d %H:%M")
    edate = datetime.strptime("{} {}".format(end_date, end_time), "%Y-%m-%d %H:%M")
    idate = idate.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
    edate = edate.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
    idate = idate.astimezone(ZoneInfo("UTC"))
    edate = edate.astimezone(ZoneInfo("UTC"))

    obj.ini_date = idate
    obj.end_date = edate
    obj.finish = True if finish != "" else False
    obj.save()
    return render(request, "assistances-list.html", {"item_list": get_assistances(request)})

@group_required("Administradores",)
def assistances_remove(request):
    obj = get_or_none(Assistance, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    return render(request, "assistances-list.html", {"item_list": get_assistances(request)})

def assistances_client(request, client_id):
    return render(request, "assistances-client-error.html", {})

'''
    EMPLOYEES
'''
def get_employees(request):

    search_value = get_session(request, "s_emp_name")
    search_comp = get_session(request, "s_emp_comp")
    kwargs = {}
    if search_value != "" or search_comp != "":
        if search_value != "":
            kwargs["name__unaccent__icontains"] = search_value
        if search_comp != "":
            kwargs["timetables__client__name__unaccent__icontains"] = search_comp
        return Employee.objects.filter(**kwargs)
    return Employee.objects.all()
    #filters_to_search = ["name__icontains",]
    #full_query = Q()
    #if search_value != "":
    #    for myfilter in filters_to_search:
    #        full_query |= Q(**{myfilter: search_value})
    #return Employee.objects.filter(full_query)

@group_required("Administradores",)
def employees(request):
    init_session_date(request, "s_emp_idate")
    init_session_date(request, "s_emp_edate")
    return render(request, "employees/employees.html", {"items": get_employees(request)})

@group_required("Administradores",)
def employees_list(request):
    return render(request, "employees/employees-list.html", {"items": get_employees(request)})

@group_required("Administradores",)
def employees_search(request):
    set_session(request, "s_emp_name", get_param(request.GET, "s_emp_name"))
    set_session(request, "s_emp_comp", get_param(request.GET, "s_emp_comp"))
    set_session(request, "s_emp_idate", get_param(request.GET, "s_emp_idate"))
    set_session(request, "s_emp_edate", get_param(request.GET, "s_emp_edate"))
    return render(request, "employees/employees-list.html", {"items": get_employees(request)})

@group_required("Administradores",)
def employees_form(request):
    obj_id = get_param(request.GET, "obj_id")
    obj = get_or_none(Employee, obj_id)
    if obj == None:
        obj = Employee.objects.create()
    return render(request, "employees/employees-form.html", {'obj': obj, 'zone_list': Zone.objects.all(), 'client_list': Client.objects.all()})

@group_required("Administradores",)
def employees_remove(request):
    obj = get_or_none(Employee, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        if obj.user != None:
            obj.user.delete()
        obj.delete()
    return render(request, "employees/employees-list.html", {"items": get_employees(request)})

@group_required("Administradores",)
def employees_form_timetable(request):
    obj = get_or_none(Employee, get_param(request.GET, "obj_id"))
    #print(obj)
    if obj != None:
        client = get_or_none(Client, get_param(request.GET, "client"))
        days = request.GET.getlist("day")
        ini = get_param(request.GET, "ini")
        end = get_param(request.GET, "end")
        for day in days:
            ClientTimetable.objects.create(client=client, employee=obj, day=day, ini=ini, end=end)
    return render(request, "employees/employees-form-timetable.html", {'obj': obj, 'client_list': Client.objects.all()})

@group_required("Administradores",)
def employees_form_timetable_remove(request):
    obj = get_or_none(ClientTimetable, get_param(request.GET, "obj_id"))
    emp = None
    #print(obj)
    if obj != None:
        emp = obj.employee
        obj.delete()
    return render(request, "employees/employees-form-timetable.html", {'obj': emp, 'client_list': Client.objects.all(),})

@group_required("Administradores",)
def employees_save_email(request):
    try:
        obj = get_or_none(Employee, get_param(request.GET, "obj_id"))
        obj.email = get_param(request.GET, "value")
        obj.save()
        obj.save_user()
        return HttpResponse("Saved!")
    except Exception as e:
        return HttpResponse("Error: {}".format(e))

@group_required("Administradores",)
def employees_export(request):
    header = ['Nombre', 'Teléfono', 'Email', 'PIN', 'DNI', 'Horas trabajadas', 'Minutos trabajados']
    values = []
    items = get_employees(request)
    for item in items:
        hours, minutes = item.worked_time(request.session["s_emp_idate"], request.session["s_emp_edate"])
        row = [item.name, item.phone, item.email, item.pin, item.dni, hours, minutes]
        values.append(row)
    return csv_export(header, values, "empleados")

@group_required("admins")
def employees_import_csv(request):
    return render(request, "employees/import-csv.html", {})

@group_required("Administradores",)
def employees_import(request):
    f = request.FILES["file"]
    lines = f.read().decode('utf-8').splitlines()
    i = 0
    for line in lines:
        if i > 0:
            l = line.split(";")
            obj = Employee.objects.filter(dni=l[2]).first()
            if obj == None:
                obj = Employee.objects.create(dni=l[2])
            print(l)
            obj.name = "{} {}".format(l[0], l[1])
            obj.phone = l[4]
            obj.email = l[3]
            obj.dni = l[2]
            obj.save()
            #obj, created = Employee.objects.get_or_create(pin=dni, dni=dni, name=name, phone=phone, email=email)
            try:
                obj.save_user()
            except Exception as e:
                print(e)
        i += 1
    return redirect("employees")

'''
    CLIENTS
'''
def get_clients(request):
    search_value = get_session(request, "s_cli_name")
    filters_to_search = ["name__unaccent__icontains",]
    full_query = Q()
    if search_value != "":
        for myfilter in filters_to_search:
            full_query |= Q(**{myfilter: search_value})
    return Client.objects.filter(full_query).order_by("-id")[:50]

@group_required("Administradores",)
def clients(request):
    return render(request, "clients/clients.html", {"items": get_clients(request)})

@group_required("Administradores",)
def clients_list(request):
    return render(request, "clients/clients-list.html", {"items": get_clients(request)})

@group_required("Administradores",)
def clients_search(request):
    set_session(request, "s_cli_name", get_param(request.GET, "s_cli_name"))
    return render(request, "clients/clients-list.html", {"items": get_clients(request)})

@group_required("Administradores",)
def clients_form(request):
    obj_id = get_param(request.GET, "obj_id")
    obj = get_or_none(Client, obj_id)
    new = False
    if obj == None:
        obj = Client.objects.create()
        url = "{}{}".format(ACCESS_PATH, obj.id)
        path = os.path.join(settings.BASE_DIR, "static", "images", "logo-asistencia-canaria.jpg")
        img_data = ContentFile(generate_qr(url, path))
        obj.qr.save('qr_{}.png'.format(obj.id), img_data, save=True)
        new = True
    return render(request, "clients/clients-form.html", {'obj': obj, 'new': new, 'emp_list': Employee.objects.all()})

@group_required("Administradores",)
def clients_form_timetable(request):
    obj = get_or_none(Client, get_param(request.GET, "obj_id"))
    #print(obj)
    if obj != None:
        emp = get_or_none(Employee, get_param(request.GET, "employee"))
        days = request.GET.getlist("day")
        ini = get_param(request.GET, "ini")
        end = get_param(request.GET, "end")
        for day in days:
            ClientTimetable.objects.create(client=obj, employee=emp, day=day, ini=ini, end=end)
    return render(request, "clients/clients-form-timetable.html", {'obj': obj, 'emp_list': Employee.objects.all()})

@group_required("Administradores",)
def clients_remove(request):
    obj = get_or_none(Client, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.qr.delete(save=True)
        obj.delete()
    return render(request, "clients/clients-list.html", {"items": get_clients(request)})

@group_required("Administradores",)
def clients_form_timetable_remove(request):
    obj = get_or_none(ClientTimetable, get_param(request.GET, "obj_id"))
    client = None
    #print(obj)
    if obj != None:
        client = obj.client
        obj.delete()
    return render(request, "clients/clients-form-timetable.html", {'obj': client, 'emp_list': Employee.objects.all(),})

@group_required("Administradores",)
def clients_print_all_qr(request):
    return render(request, "clients/clients-print-all-qr.html", {"item_list": Client.objects.filter(inactive=False)})

@group_required("Administradores",)
def clients_print_qr(request, obj_id):
    return render(request, "clients/clients-print-qr.html", {"obj": get_or_none(Client, obj_id)})

@group_required("Administradores",)
def clients_assistances(request, obj_id):
    return render(request, "clients/clients-assistances.html", {"obj": get_or_none(Client, obj_id)})

@group_required("admins")
def clients_import_csv(request):
    return render(request, "clients/import-csv.html", {})

@group_required("admins")
def clients_import(request):
    try:
        f = request.FILES["file"]

        lines = f.read().decode('utf-8').splitlines()
        i = 0
        for line in lines:
            if i > 0:
                l = line.split(";")
                print(l)
                obj = Client.objects.filter(code=l[1]).first()
                if obj == None:
                    obj = Client.objects.create(code=l[1])
                obj.name = l[0]
                obj.addess = l[2]
                obj.phone = l[3]
                obj.email = l[4]
                obj.save()
            i += 1
        return redirect("clients")
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

'''
    REPORT
'''
def get_total_duration(item_list):
    total = 0
    for item in item_list:
        total += get_int(item.duration)
    return total

def get_report(request):
    cli = get_session(request, "s_rep_cli")
    emp = get_session(request, "s_rep_emp")
    i_date = datetime.strptime("{} 00:00".format(get_session(request, "s_rep_idate")), "%Y-%m-%d %H:%M")
    e_date = datetime.strptime("{} 23:59".format(get_session(request, "s_rep_edate")), "%Y-%m-%d %H:%M")

    kwargs = {"ini_date__range": (i_date, e_date)}
    if cli != "":
        kwargs["client__name__unaccent__icontains"] = cli
    if emp != "":
        kwargs["employee__name__unaccent__icontains"] = emp

    return Assistance.objects.filter(**kwargs)

@group_required("Administradores",)
def report(request):
    init_session_date(request, "s_rep_idate")
    init_session_date(request, "s_rep_edate")
    return render(request, "report/report.html", {"items": []})
    #return render(request, "report/report.html", {"items": get_report(request)})

@group_required("Administradores",)
def report_list(request):
    item_list = get_report(request)
    return render(request, "report/report-list.html", {"items": item_list, "duration": get_total_duration(item_list)})

@group_required("Administradores",)
def report_search(request):
    set_session(request, "s_rep_emp", get_param(request.GET, "s_rep_emp"))
    set_session(request, "s_rep_cli", get_param(request.GET, "s_rep_cli"))
    set_session(request, "s_rep_idate", get_param(request.GET, "s_rep_idate"))
    set_session(request, "s_rep_edate", get_param(request.GET, "s_rep_edate"))
    item_list = get_report(request)
    return render(request, "report/report-list.html", {"items": item_list, "duration": get_total_duration(item_list)})

@group_required("Administradores",)
def report_export(request):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    header = ['Cliente', 'Empleado', 'Fecha de inicio', 'Fecha de fin', 'Duración del servicio', 'Finalizada']
    values = []
    items = get_report(request)
    for item in items:
        ini_date = item.ini_date.astimezone(ZoneInfo("Atlantic/Canary"))
        idate = ini_date.strftime("%d-%m-%Y %H:%M")
        end_date = item.end_date.astimezone(ZoneInfo("Atlantic/Canary"))
        edate = end_date.strftime("%d-%m-%Y %H:%M")
        finish = "Si" if item.finish else "No"
        client = item.client.name if item.client != None else ""
        emp = item.employee.name if item.employee != None else ""
        row = [client, emp, idate, edate, item.duration, finish]
        values.append(row)
    return csv_export(header, values, "empleados")

@group_required("Administradores",)
def report_search_emp(request):
    try:
        value = get_param(request.GET, "value")
        items = Employee.objects.filter(name__unaccent__icontains=value) if value != "" else []
        return render(request, "report/report-search-emp.html", {'items': items, 'value':value})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("Administradores",)
def report_search_cli(request):
    try:
        value = get_param(request.GET, "value")
        items = Client.objects.filter(name__unaccent__icontains=value) if value != "" else []
        return render(request, "report/report-search-cli.html", {'items': items, 'value':value})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


'''
    EMPLOYEES
'''
@group_required("Administradores",)
def employee(request, obj_id):
    idate = datetime.today().replace(day=1)
    last_day = calendar.monthrange(idate.year, idate.month)[1]
    edate = idate.replace(day=last_day)
    set_session(request, "s_employee_idate", idate.strftime("%Y-%m-%d"))
    set_session(request, "s_employee_edate", edate.strftime("%Y-%m-%d"))
    emp = get_or_none(Employee, obj_id)
    return render(request, "employee/clients.html", {"obj": emp})

@group_required("Administradores",)
def employee_search(request):
    obj_id = get_param(request.GET, "obj_id")
    set_session(request, "s_employee_idate", get_param(request.GET, "s_employee_idate"))
    set_session(request, "s_employee_edate", get_param(request.GET, "s_employee_edate"))
    return redirect(reverse('employee', kwargs={'obj_id': obj_id}))

@group_required("Administradores",)
def employee_search_client(request):
    try:
        value = get_param(request.GET, "value")
        obj = get_or_none(Employee, get_param(request.GET, "obj_id"))
        items = []
        if value != "":
            items = Client.objects.filter(name__unaccent__icontains=value)
        return render(request, "employee/client-search-list.html", {'items': items, 'obj': obj, 'value':value})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("Administradores",)
def employee_form_timetable(request):
    obj = get_or_none(Employee, get_param(request.GET, "obj_id"))
    if obj != None:
        client = get_or_none(Client, get_param(request.GET, "client_id"))
        days = request.GET.getlist("day")
        ini = get_param(request.GET, "ini")
        end = get_param(request.GET, "end")
        for day in days:
            ClientTimetable.objects.create(client=client, employee=obj, day=day, ini=ini, end=end)
    return redirect(reverse('employee', kwargs={'obj_id': obj.id}))
    #return render(request, "employees/employees-form-timetable.html", {'obj': obj, 'client_list': Client.objects.all()})

@group_required("Administradores",)
def employee_form_timetable_remove(request, obj_id):
    obj = get_or_none(ClientTimetable, obj_id)
    emp = None
    if obj != None:
        emp = obj.employee
        obj.delete()
    return redirect(reverse('employee', kwargs={'obj_id': emp.id}))


'''
    INCIDENTS
'''
def get_incidents(request):
    i_date = datetime.strptime("{} 00:00".format(get_session(request, "s_inc_idate")), "%Y-%m-%d %H:%M")
    e_date = datetime.strptime("{} 23:59".format(get_session(request, "s_inc_edate")), "%Y-%m-%d %H:%M")
    status = get_session(request, "s_inc_status")
    emp = get_session(request, "s_inc_emp")

    kwargs = {"creation_date__range": (i_date, e_date),}
    if status != "": 
        kwargs['closed'] = True if status == "True" else False
    if emp != "": 
        user_list = [item.user for item in Employee.objects.filter(name__unaccent__icontains=emp)]
        kwargs['owner__in'] = user_list
    return Incident.objects.filter(**kwargs)

@group_required("Administradores",)
def incidents(request):
    init_session_date(request, "s_inc_idate")
    init_session_date(request, "s_inc_edate")
    set_session(request, "s_inc_status", "False")
    return render(request, "incidents/incidents.html", {"items": get_incidents(request)})

@group_required("Administradores",)
def incidents_list(request):
    item_list = get_incidents(request)
    return render(request, "incidents/incidents-list.html", {"items": item_list})

@group_required("Administradores",)
def incidents_search(request):
    set_session(request, "s_inc_idate", get_param(request.GET, "s_inc_idate"))
    set_session(request, "s_inc_edate", get_param(request.GET, "s_inc_edate"))
    set_session(request, "s_inc_status", get_param(request.GET, "s_inc_status"))
    set_session(request, "s_inc_emp", get_param(request.GET, "s_inc_emp"))
    item_list = get_incidents(request)
    return render(request, "incidents/incidents-list.html", {"items": item_list,})

@group_required("Administradores",)
def incidents_form(request):
    obj = get_or_none(Incident, get_param(request.GET, "obj_id"))
    if obj == None:
        return render(request, "error_exception.html", {'exc': 'Object not found!'})
    return render(request, "incidents/incidents-form.html", {'obj': obj,})


