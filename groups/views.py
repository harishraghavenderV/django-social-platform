from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from .models import Group, GroupMembership
from .forms import GroupForm
from posts.models import Post


@login_required
def group_list(request):
    query = request.GET.get('q', '')
    if query:
        groups = Group.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    else:
        groups = Group.objects.all()

    groups = groups.annotate(members=Count('memberships'))

    # User's groups
    my_groups = Group.objects.filter(
        memberships__user=request.user
    ).annotate(members=Count('memberships'))

    return render(request, 'groups/group_list.html', {
        'groups': groups,
        'my_groups': my_groups,
        'query': query,
    })


@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    is_member = GroupMembership.objects.filter(group=group, user=request.user).exists()
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()
    members = GroupMembership.objects.filter(group=group).select_related('user')
    posts = Post.objects.filter(group=group).order_by('-created_at')

    return render(request, 'groups/group_detail.html', {
        'group': group,
        'is_member': is_member,
        'membership': membership,
        'members': members,
        'posts': posts,
    })


@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.save()
            # Creator is automatically admin
            GroupMembership.objects.create(
                group=group, user=request.user, role='admin'
            )
            return redirect('group_detail', group_id=group.id)
    else:
        form = GroupForm()
    return render(request, 'groups/create_group.html', {'form': form})


@login_required
def join_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if not GroupMembership.objects.filter(group=group, user=request.user).exists():
        GroupMembership.objects.create(group=group, user=request.user, role='member')
    return redirect('group_detail', group_id=group.id)


@login_required
def leave_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    GroupMembership.objects.filter(group=group, user=request.user).exclude(role='admin').delete()
    return redirect('group_list')


@login_required
def group_post_create(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if not GroupMembership.objects.filter(group=group, user=request.user).exists():
        return redirect('group_detail', group_id=group.id)

    if request.method == 'POST':
        content = request.POST.get('content', '')
        image = request.FILES.get('image')
        if content or image:
            post = Post.objects.create(
                author=request.user,
                content=content,
                image=image,
                group=group,
            )
    return redirect('group_detail', group_id=group.id)
