from core.utils.file_processor.file_export_util import Echo, FileExport
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse


@login_required
def diagram_view(request, content_type_id, object_id):
    # Get the content type and the object
    content_type = get_object_or_404(ContentType, id=content_type_id)
    model_class = content_type.model_class()
    obj = get_object_or_404(model_class, id=object_id)

    # Generate Mermaid diagram code based on the object (customize this as needed)
    mermaid_code = obj.to_mermaid().to_graph()
    # Render the template with the generated code
    return render(request, "core/diagram.html", {"mermaid_code": mermaid_code})


@login_required
def user_permissions_tree(request):
    user_ids = request.GET.getlist('ids')

    if user_ids:
        users = User.objects.filter(id__in=user_ids).prefetch_related('groups__permissions', 'user_permissions')
    else:
        users = User.objects.prefetch_related('groups__permissions', 'user_permissions').all()

    tree_data = []
    for user in users:
        user_node = {
            'text': f'User: {user.username}',
            'a_attr': {'href': reverse('admin:auth_user_change', args=[user.id]), 'target': '_blank'},
            'children': []
        }

        for group in user.groups.all():
            group_node = {
                'text': f'Group: {group.name}',
                'a_attr': {'href': reverse('admin:auth_group_change', args=[group.id]), 'target': '_blank'},
                'children': []
            }

            permissions = {}
            for perm in group.permissions.all():
                code = perm.codename.split('_')[0]
                if code not in permissions:
                    permissions[code] = []
                permissions[code].append(perm)

            for code, perms in permissions.items():
                group_node['children'].append({
                    'text': f'{code}',
                    'children': [
                        {
                            'text': perm.name,
                            'a_attr': {
                                'href': reverse('admin:auth_permission_change', args=[perm.id]),
                                'target': '_blank'
                            }
                        }
                        for perm in perms
                    ]
                })

            # for perm in group.permissions.all():
            #     group_node['children'].append({
            #         'text': f'{perm.name} ({perm.codename})',
            #         'a_attr': {'href': reverse('admin:auth_permission_change', args=[perm.id]), 'target': '_blank'}
            #     })

            user_node['children'].append(group_node)

        for perm in user.user_permissions.all():
            user_node['children'].append({
                'text': f'Permission: {perm.name} ({perm.codename})',
                'a_attr': {'href': reverse('admin:auth_permission_change', args=[perm.id]), 'target': '_blank'}
            })

        tree_data.append(user_node)

    return JsonResponse(tree_data, safe=False)


@login_required
def download_file(request):
    if request.method != 'GET':
        return HttpResponse(status=405)

    if request.GET.get('file', None) is None:
        return HttpResponse('The \"file\" query parameter is required', status=400)

    # Look up file exporter from registry (allows domain apps to register exporters)
    from core.utils.file_export_registry import get_file_exporter

    file_name = request.GET.get('file').lower()
    exporter_class = get_file_exporter(file_name)

    if exporter_class is None:
        return HttpResponse(
            f'Provided query parameter "file" value "{file_name}" is not a valid choice.',
            status=400
        )

    export_config: FileExport = exporter_class()
    validation_error = export_config.validate_params(request)
    if validation_error:
        return validation_error

    content_type = export_config.get_content_type()

    return StreamingHttpResponse(
        streaming_content=(export_config.iter_items(export_config.get_queryset(request), Echo())),
        content_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{export_config.get_filename(request.GET)}"'},
    )


@login_required
def compare_user_permissions(request):
    """
    Main view for comparing user permissions.
    Shows a searchable interface to select base user and users to compare.
    """
    # Get pre-selected user IDs if coming from admin action (optional now)
    preselected_user_ids = request.GET.getlist('ids')

    context = {
        'preselected_user_ids': preselected_user_ids,
    }

    return render(request, "core/compare_user_permissions.html", context)


@login_required
def search_users(request):
    """
    HTMX endpoint to search users for the comparison tool.
    """
    search_query = request.GET.get('q', '').strip()

    if len(search_query) < 2:
        users = User.objects.none()
    else:
        users = User.objects.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        ).order_by('username')[:100]  # Limit to 100 results

    context = {
        'users': users,
        'search_query': search_query,
    }

    return render(request, "core/partials/user_search_results.html", context)


@login_required
def compare_user_permissions_data(request):
    """
    HTMX endpoint that returns the comparison data when users are selected.
    Accepts both GET and POST requests.
    """
    # Support both GET and POST
    if request.method == 'POST':
        base_user_id = request.POST.get('base_user_id')
        user_ids = request.POST.getlist('compared_user_ids')
    else:
        base_user_id = request.GET.get('base_user_id')
        user_ids = request.GET.getlist('ids')

    if not base_user_id:
        return HttpResponse("Please select a base user.", status=400)

    if not user_ids or len(user_ids) < 1:
        return HttpResponse("Please select at least one user to compare.", status=400)

    # Get all users
    base_user = get_object_or_404(User, id=base_user_id)
    compared_users = User.objects.filter(id__in=user_ids).exclude(id=base_user_id).prefetch_related('groups')
    all_groups = Group.objects.all().prefetch_related('permissions').order_by('name')

    # Build comparison data
    base_user_groups = set(base_user.groups.all())
    compared_users_data = []

    for user in compared_users:
        user_groups = set(user.groups.all())
        compared_users_data.append({
            'user': user,
            'groups': user_groups
        })

    # Build group comparison matrix
    group_comparisons = []
    for group in all_groups:
        comparison = {
            'group': group,
            'in_base_user': group in base_user_groups,
            'compared_users_status': []
        }

        for user_data in compared_users_data:
            comparison['compared_users_status'].append({
                'user': user_data['user'],
                'has_group': group in user_data['groups']
            })

        group_comparisons.append(comparison)

    context = {
        'base_user': base_user,
        'compared_users': compared_users,
        'group_comparisons': group_comparisons,
    }

    return render(request, "core/partials/comparison_table.html", context)


@login_required
def search_groups(request):
    """
    HTMX endpoint to search groups for the comparison tool.
    """
    search_query = request.GET.get('q', '').strip()
    if search_query:
        groups = Group.objects.filter(
            Q(name__icontains=search_query) |
            Q(permissions__name__icontains=search_query),
        ).distinct().order_by('name')
    else:
        # Load all groups if no search query
        groups = Group.objects.all().order_by('name')

    context = {
        'groups': groups,
        'search_query': search_query,
    }

    return render(request, "core/partials/group_search_results.html", context)


@login_required
def toggle_group_membership(request):
    """
    Endpoint to add or remove a user from a group.
    Accepts POST requests with user_id, group_id, and add (true/false) parameters.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    user_id = request.POST.get('user_id')
    group_id = request.POST.get('group_id')
    add = request.POST.get('add', '').lower() == 'true'

    if not user_id or not group_id:
        return JsonResponse({'success': False, 'error': 'Missing user_id or group_id'}, status=400)

    try:
        user = get_object_or_404(User, id=user_id)
        group = get_object_or_404(Group, id=group_id)

        if add:
            # Add user to group
            user.groups.add(group)
            action = 'added to'
        else:
            # Remove user from group
            user.groups.remove(group)
            action = 'removed from'

        return JsonResponse({
            'success': True,
            'message': f'User {user.username} {action} group {group.name}'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def compare_group_permissions_data(request):
    """
    HTMX endpoint that returns the comparison data for groups.
    Accepts both GET and POST requests.
    """
    # Support both GET and POST
    if request.method == 'POST':
        base_group_id = request.POST.get('base_group_id')
        group_ids = request.POST.getlist('compared_group_ids')
    else:
        base_group_id = request.GET.get('base_group_id')
        group_ids = request.GET.getlist('ids')

    if not base_group_id:
        return HttpResponse("Please select a base group.", status=400)

    if not group_ids or len(group_ids) < 1:
        return HttpResponse("Please select at least one group to compare.", status=400)

    # Get all groups with permissions
    base_group = get_object_or_404(Group.objects.prefetch_related('permissions'), id=base_group_id)
    compared_groups = Group.objects.filter(id__in=group_ids).exclude(id=base_group_id).prefetch_related('permissions')

    # Get all unique permissions across all groups
    from django.contrib.auth.models import Permission
    all_permission_ids = set()

    # Add base group permissions
    all_permission_ids.update(base_group.permissions.values_list('id', flat=True))

    # Add compared groups permissions
    for group in compared_groups:
        all_permission_ids.update(group.permissions.values_list('id', flat=True))

    # Get all permissions sorted by content type and name
    all_permissions = Permission.objects.filter(
        id__in=all_permission_ids
    ).select_related('content_type').order_by('content_type__app_label', 'content_type__model', 'codename')

    # Build comparison data
    base_group_permissions = set(base_group.permissions.all())
    compared_groups_data = []

    for group in compared_groups:
        group_permissions = set(group.permissions.all())
        compared_groups_data.append({
            'group': group,
            'permissions': group_permissions
        })

    # Build permission comparison matrix
    permission_comparisons = []
    for permission in all_permissions:
        comparison = {
            'permission': permission,
            'in_base_group': permission in base_group_permissions,
            'compared_groups_status': []
        }

        for group_data in compared_groups_data:
            comparison['compared_groups_status'].append({
                'group': group_data['group'],
                'has_permission': permission in group_data['permissions']
            })

        permission_comparisons.append(comparison)

    context = {
        'base_group': base_group,
        'compared_groups': compared_groups,
        'permission_comparisons': permission_comparisons,
    }

    return render(request, "core/partials/group_comparison_table.html", context)


@login_required
def toggle_permission_in_group(request):
    """
    Endpoint to add or remove a permission from a group.
    Accepts POST requests with group_id, permission_id, and add (true/false) parameters.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    group_id = request.POST.get('group_id')
    permission_id = request.POST.get('permission_id')
    add = request.POST.get('add', '').lower() == 'true'

    if not group_id or not permission_id:
        return JsonResponse({'success': False, 'error': 'Missing group_id or permission_id'}, status=400)

    try:
        from django.contrib.auth.models import Permission

        group = get_object_or_404(Group, id=group_id)
        permission = get_object_or_404(Permission, id=permission_id)

        if add:
            # Add permission to group
            group.permissions.add(permission)
            action = 'added to'
        else:
            # Remove permission from group
            group.permissions.remove(permission)
            action = 'removed from'

        return JsonResponse({
            'success': True,
            'message': f'Permission {permission.codename} {action} group {group.name}'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
