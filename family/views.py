from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Person, Relationship
from collections import deque

# ─── Reverse relationship map ───
REVERSE_RELATION = {
    'father': 'child',
    'mother': 'child',
    'son': 'parent',
    'daughter': 'parent',
    'brother': 'sibling',
    'sister': 'sibling',
    'husband': 'wife',
    'wife': 'husband',
    'child': 'parent',
    'parent': 'child',
    'sibling': 'sibling',
}

# ─── Smart relationship resolver ───
def resolve_relationship(path_relations, gender):
    """
    Resolves relationship name from a list of relation steps.
    Example: ['father', 'sister'] -> Aunt
    """
    if not path_relations:
        return ('Same Person', 'அதே நபர்')

    # Single step
    if len(path_relations) == 1:
        rel = path_relations[0]
        single_map = {
            'father':  ('Father', 'அப்பா'),
            'mother':  ('Mother', 'அம்மா'),
            'brother': ('Brother', 'அண்ணன்/தம்பி'),
            'sister':  ('Sister', 'அக்கா/தங்கை'),
            'husband': ('Husband', 'கணவன்'),
            'wife':    ('Wife', 'மனைவி'),
            'son':     ('Son', 'மகன்'),
            'daughter':('Daughter', 'மகள்'),
            'child':   ('Child', 'குழந்தை'),
            'parent':  ('Parent', 'பெற்றோர்'),
            'sibling': ('Sibling', 'உடன்பிறந்தவர்'),
        }
        return single_map.get(rel, ('Relative', 'உறவினர்'))

    # Two steps
    if len(path_relations) == 2:
        step1, step2 = path_relations
        two_step_map = {
            ('father', 'brother'):   ('Uncle', 'சித்தப்பா/பெரியப்பா'),
            ('father', 'sister'):    ('Aunt', 'அத்தை'),
            ('father', 'father'):    ('Grandfather', 'தாத்தா'),
            ('father', 'mother'):    ('Grandmother', 'பாட்டி'),
            ('father', 'wife'):      ('Mother', 'அம்மா'),
            ('father', 'child'):     ('Sibling', 'உடன்பிறந்தவர்'),
            ('father', 'son'):       ('Brother', 'அண்ணன்/தம்பி'),
            ('father', 'daughter'):  ('Sister', 'அக்கா/தங்கை'),
            ('mother', 'brother'):   ('Maternal Uncle', 'மாமா'),
            ('mother', 'sister'):    ('Maternal Aunt', 'மாமி'),
            ('mother', 'father'):    ('Grandfather', 'தாத்தா'),
            ('mother', 'mother'):    ('Grandmother', 'பாட்டி'),
            ('mother', 'husband'):   ('Father', 'அப்பா'),
            ('mother', 'child'):     ('Sibling', 'உடன்பிறந்தவர்'),
            ('mother', 'son'):       ('Brother', 'அண்ணன்/தம்பி'),
            ('mother', 'daughter'):  ('Sister', 'அக்கா/தங்கை'),
            ('brother', 'son'):      ('Nephew', 'மருமகன்'),
            ('brother', 'daughter'): ('Niece', 'மருமகள்'),
            ('brother', 'wife'):     ('Sister-in-law', 'மச்சினி'),
            ('sister', 'son'):       ('Nephew', 'மருமகன்'),
            ('sister', 'daughter'):  ('Niece', 'மருமகள்'),
            ('sister', 'husband'):   ('Brother-in-law', 'மாமனார்'),
            ('son', 'son'):          ('Grandson', 'பேரன்'),
            ('son', 'daughter'):     ('Granddaughter', 'பேத்தி'),
            ('daughter', 'son'):     ('Grandson', 'பேரன்'),
            ('daughter', 'daughter'):('Granddaughter', 'பேத்தி'),
            ('child', 'child'):      ('Grandchild', 'பேரக்குழந்தை'),
            ('parent', 'parent'):    ('Grandparent', 'தாத்தா/பாட்டி'),
            ('parent', 'sibling'):   ('Uncle/Aunt', 'சித்தப்பா/அத்தை'),
            ('sibling', 'child'):    ('Nephew/Niece', 'மருமகன்/மருமகள்'),
            ('sibling', 'parent'):   ('Parent', 'பெற்றோர்'),
            ('husband', 'father'):   ('Father-in-law', 'மாமனார்'),
            ('husband', 'mother'):   ('Mother-in-law', 'மாமியார்'),
            ('husband', 'brother'):  ('Brother-in-law', 'நாத்தனார்'),
            ('husband', 'sister'):   ('Sister-in-law', 'நாத்தனார்'),
            ('wife', 'father'):      ('Father-in-law', 'மாமனார்'),
            ('wife', 'mother'):      ('Mother-in-law', 'மாமியார்'),
            ('wife', 'brother'):     ('Brother-in-law', 'மச்சான்'),
            ('wife', 'sister'):      ('Sister-in-law', 'மச்சினி'),
            ('wife', 'son'):         ('Son', 'மகன்'),
            ('wife', 'daughter'):    ('Daughter', 'மகள்'),
            ('husband', 'son'):      ('Son', 'மகன்'),
            ('husband', 'daughter'): ('Daughter', 'மகள்'),
        }
        result = two_step_map.get((step1, step2))
        if result:
            return result

    # Three steps
    if len(path_relations) == 3:
        step1, step2, step3 = path_relations
        three_step_map = {
            ('father', 'brother', 'son'):      ('Cousin', 'உறவினர்'),
            ('father', 'brother', 'daughter'): ('Cousin', 'உறவினர்'),
            ('father', 'sister', 'son'):       ('Cousin', 'உறவினர்'),
            ('father', 'sister', 'daughter'):  ('Cousin', 'உறவினர்'),
            ('mother', 'brother', 'son'):      ('Cousin', 'உறவினர்'),
            ('mother', 'brother', 'daughter'): ('Cousin', 'உறவினர்'),
            ('mother', 'sister', 'son'):       ('Cousin', 'உறவினர்'),
            ('mother', 'sister', 'daughter'):  ('Cousin', 'உறவினர்'),
            ('father', 'father', 'brother'):   ('Great Uncle', 'பெரிய தாத்தா'),
            ('father', 'father', 'sister'):    ('Great Aunt', 'பெரிய பாட்டி'),
        }
        result = three_step_map.get((step1, step2, step3))
        if result:
            return result

    return ('Relative', 'உறவினர்')
# ─── Inference Rules ───
def infer_relationships(user):
    def get_or_create_rel(p1, p2, rel_type):
        if p1.id == p2.id:
            return
        exists = Relationship.objects.filter(
            user=user,
            person1=p1,
            person2=p2,
            relation_type=rel_type
        ).exists()
        if not exists:
            Relationship.objects.create(
                user=user,
                person1=p1,
                person2=p2,
                relation_type=rel_type
            )

    def parent_rel(person):
        return 'father' if person.gender == 'male' else 'mother'

    def child_rel(person):
        return 'son' if person.gender == 'male' else 'daughter'

    def sibling_rel(person):
        return 'brother' if person.gender == 'male' else 'sister'

    changed = True
    while changed:
        changed = False
        rels = list(Relationship.objects.filter(user=user))
        count_before = len(rels)

        for rel in rels:
            A = rel.person1
            B = rel.person2
            rel_type = rel.relation_type

            # ── Rule 1: Spouse reverse ──
            if rel_type == 'husband':
                # A husband B → B wife A
                get_or_create_rel(B, A, 'wife')

            if rel_type == 'wife':
                # A wife B → B husband A
                get_or_create_rel(B, A, 'husband')

            # ── Rule 2: Parent → child reverse ──
            if rel_type == 'father':
                # A father B → B son/daughter A
                get_or_create_rel(B, A, child_rel(B))

            if rel_type == 'mother':
                # A mother B → B son/daughter A
                get_or_create_rel(B, A, child_rel(B))

            # ── Rule 3: Child → parent reverse ──
            if rel_type == 'son':
                # A son B → B father/mother A (based on A's gender)
                get_or_create_rel(B, A, parent_rel(B))

            if rel_type == 'daughter':
                # A daughter B → B father/mother A
                get_or_create_rel(B, A, parent_rel(B))

            # ── Rule 4: Sibling reverse ──
            if rel_type == 'brother':
                get_or_create_rel(B, A, sibling_rel(B))

            if rel_type == 'sister':
                get_or_create_rel(B, A, sibling_rel(B))

            # ── Rule 5: Spouse shares children (BLOOD only) ──
            if rel_type in ('husband', 'wife'):
                spouse = B
                # Find ONLY blood children of A (not inferred)
                children_of_a = Relationship.objects.filter(
                    user=user,
                    person1=A,
                    relation_type__in=('son', 'daughter')
                )
                for cr in children_of_a:
                    child = cr.person2
                    # Only if child is NOT spouse's sibling/parent
                    is_sibling = Relationship.objects.filter(
                        user=user,
                        person1=spouse,
                        person2=child,
                        relation_type__in=('brother','sister')
                    ).exists()
                    is_parent = Relationship.objects.filter(
                        user=user,
                        person1=spouse,
                        person2=child,
                        relation_type__in=('father','mother')
                    ).exists()
                    if not is_sibling and not is_parent and child.id != spouse.id:
                        get_or_create_rel(spouse, child, child_rel(child))

            # ── Rule 6: Siblings share parents (BLOOD only) ──
            if rel_type in ('brother', 'sister'):
                sibling = B
                parents_of_a = Relationship.objects.filter(
                    user=user,
                    person1=A,
                    relation_type__in=('father','mother')
                )
                for pr in parents_of_a:
                    parent = pr.person2
                    if parent.id != sibling.id:
                        get_or_create_rel(sibling, parent, parent_rel(parent))
                        get_or_create_rel(parent, sibling, child_rel(sibling))

            # ── Rule 7: Same parent = siblings ──
            if rel_type in ('father', 'mother'):
                parent = A
                child = B
                siblings = Relationship.objects.filter(
                    user=user,
                    person1=parent,
                    relation_type__in=('son','daughter')
                ).exclude(person2=child)
                for sr in siblings:
                    sibling = sr.person2
                    if sibling.id != child.id:
                        get_or_create_rel(child, sibling, sibling_rel(sibling))
                        get_or_create_rel(sibling, child, sibling_rel(child))

        count_after = Relationship.objects.filter(user=user).count()
        if count_after > count_before:
            changed = True

# ─── Build bidirectional graph ───
def build_graph(user):
    relationships = Relationship.objects.filter(user=user)
    graph = {}
    for rel in relationships:
        if rel.person1_id not in graph:
            graph[rel.person1_id] = []
        graph[rel.person1_id].append((rel.person2_id, rel.relation_type))

        if rel.person2_id not in graph:
            graph[rel.person2_id] = []
        reverse = REVERSE_RELATION.get(rel.relation_type, 'relative')
        graph[rel.person2_id].append((rel.person1_id, reverse))
    return graph

# ─── BFS Algorithm ───
def bfs_find_path(graph, start_id, end_id):
    if start_id == end_id:
        return [], []
    visited = {start_id}
    queue = deque([(start_id, [], [])])
    while queue:
        current, path_ids, path_rels = queue.popleft()
        for neighbor, rel_type in graph.get(current, []):
            if neighbor not in visited:
                new_ids = path_ids + [neighbor]
                new_rels = path_rels + [rel_type]
                if neighbor == end_id:
                    return new_ids, new_rels
                visited.add(neighbor)
                queue.append((neighbor, new_ids, new_rels))
    return None, None

# ─── Views ───
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if password1 == password2:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username, email=email, password=password1)
                login(request, user)
                return redirect('/dashboard/')
    return render(request, 'family/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/dashboard/')
    return render(request, 'family/login.html')

def logout_view(request):
    logout(request)
    return redirect('/login/')

@login_required(login_url='/login/')
def dashboard_view(request):
    member_count = Person.objects.filter(user=request.user).count()
    relationship_count = Relationship.objects.filter(user=request.user).count()
    members = Person.objects.filter(user=request.user)
    gen_map = set()
    for m in members:
        gen_map.add(m.gender)
    generation_count = max(1, member_count // 2)
    return render(request, 'family/dashboard.html', {
        'member_count': member_count,
        'relationship_count': relationship_count,
        'generation_count': generation_count,
    })

@login_required(login_url='/login/')
def members_view(request):
    members = Person.objects.filter(user=request.user)
    return render(request, 'family/members.html', {'members': members})

@login_required(login_url='/login/')
def add_member_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        gender = request.POST['gender']
        dob = request.POST.get('date_of_birth', None)
        Person.objects.create(
            user=request.user,
            name=name,
            gender=gender,
            date_of_birth=dob if dob else None
        )
        return redirect('/members/')
    return render(request, 'family/add_member.html')

@login_required(login_url='/login/')
def edit_member_view(request, pk):
    person = get_object_or_404(Person, pk=pk, user=request.user)
    if request.method == 'POST':
        person.name = request.POST['name']
        person.gender = request.POST['gender']
        dob = request.POST.get('date_of_birth', None)
        person.date_of_birth = dob if dob else None
        person.save()
        return redirect('/members/')
    return render(request, 'family/edit_member.html', {'person': person})

@login_required(login_url='/login/')
def delete_member_view(request, pk):
    person = get_object_or_404(Person, pk=pk, user=request.user)
    person.delete()
    return redirect('/members/')

@login_required(login_url='/login/')
def add_relationship_view(request):
    members = Person.objects.filter(user=request.user)
    if request.method == 'POST':
        person1_id = request.POST['person1']
        person2_id = request.POST['person2']
        relation_type = request.POST['relation_type']
        person1 = get_object_or_404(Person, pk=person1_id, user=request.user)
        person2 = get_object_or_404(Person, pk=person2_id, user=request.user)
        Relationship.objects.create(
            user=request.user,
            person1=person1,
            person2=person2,
            relation_type=relation_type
        )
        infer_relationships(request.user)
        return redirect('/relationships/')
    return render(request, 'family/add_relationship.html', {'members': members})

@login_required(login_url='/login/')
def relationships_view(request):
    relationships = Relationship.objects.filter(user=request.user)
    return render(request, 'family/relationships.html', {'relationships': relationships})

@login_required(login_url='/login/')
def delete_relationship_view(request, pk):
    rel = get_object_or_404(Relationship, pk=pk, user=request.user)
    rel.delete()
    return redirect('/relationships/')

@login_required(login_url='/login/')
def find_relationship_view(request):
    members = Person.objects.filter(user=request.user)
    result = None
    path_names = []
    person1 = None
    person2 = None

    if request.method == 'POST':
        person1_id = int(request.POST['person1'])
        person2_id = int(request.POST['person2'])
        person1 = get_object_or_404(Person, pk=person1_id, user=request.user)
        person2 = get_object_or_404(Person, pk=person2_id, user=request.user)

        graph = build_graph(request.user)
        path_ids, path_rels = bfs_find_path(graph, person1_id, person2_id)

        if path_ids is not None and len(path_rels) > 0:
            all_persons = {p.id: p for p in members}
            path_names = [person1.name] + [all_persons[pid].name for pid in path_ids]
            result = resolve_relationship(path_rels, person1.gender)
        else:
            result = ('No relationship found', 'உறவு இல்லை')

    return render(request, 'family/find_relationship.html', {
        'members': members,
        'result': result,
        'path_names': path_names,
        'person1': person1,
        'person2': person2,
    })
@login_required(login_url='/login/')
def family_tree_view(request):
    import json
    members = Person.objects.filter(user=request.user)
    relationships = Relationship.objects.filter(
        user=request.user,
        relation_type__in=('father','mother','son','daughter','husband','wife','brother','sister')
    )
    nodes = [{'id': p.id, 'name': p.name, 'gender': p.gender} for p in members]
    links = [{'source': r.person1_id, 'target': r.person2_id, 'type': r.relation_type} for r in relationships]
    members_json = [{'id': p.id, 'name': p.name, 'gender': p.gender, 'dob': str(p.date_of_birth) if p.date_of_birth else ''} for p in members]
    context = {
        'nodes': json.dumps(nodes),
        'links': json.dumps(links),
        'members_json': json.dumps(members_json),
        'members': members,
    }
    return render(request, 'family/family_tree.html', context)