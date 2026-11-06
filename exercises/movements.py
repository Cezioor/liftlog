"""Grouping built-in exercises into movement families (Movement).

Two built-in exercises belong to one family when their names differ only by equipment
words: "Barbell Step Ups", "Dumbbell Step Ups", "Smith Machine Step-up" -> "step up".
A group is applied automatically only when it is clearly one movement; anything doubtful
waits for the owner's confirmation in movement_groups.py, like the free-exercise-db
matches in Stage 1.5.

The 30 built-in Smith variants are linked to their base by hand (smith_variants.py),
and MANUAL_GROUPS joins exercises with different names; both are always applied.
"""

from collections import defaultdict
from dataclasses import dataclass, field

from django.db import transaction

from .models import Exercise, Movement
from .movement_groups import CONFIRMED_GROUPS, MANUAL_GROUPS, REJECTED_GROUPS
from .services import movement_name, stem
from .smith_variants import SMITH_VARIANTS
from .text import normalize


def movement_key(name):
    """ "Barbell Step Ups" -> "step up"; "Smith Machine Step-up" -> "step up"."""
    return " ".join(stem(word) for word in normalize(movement_name(name)).split())


@dataclass
class Group:
    key: str
    exercises: list
    doubts: list = field(default_factory=list)  # empty = clearly one movement

    def describe(self):
        members = ", ".join(f"{e.name} [{e.get_equipment_display()}]" for e in self.exercises)
        return f"{self.key}: {members}"


def _doubts(exercises):
    doubts = []
    equipment = [e.equipment for e in exercises]
    if len(set(equipment)) < len(equipment):
        doubts.append("the same equipment twice")
    if len({e.muscle_group for e in exercises}) > 1:
        doubts.append("different muscle groups")
    if len({e.category for e in exercises}) > 1:
        doubts.append("different categories")
    if len({e.is_unilateral for e in exercises}) > 1:
        doubts.append("one side vs both sides")
    return doubts


def name_groups(exercises=None):
    """Groups of 2+ built-ins with the same movement key, each with its doubts."""
    if exercises is None:
        exercises = Exercise.objects.filter(owner=None).order_by("name")
    by_key = defaultdict(list)
    for exercise in exercises:
        by_key[movement_key(exercise.name)].append(exercise)
    return [
        Group(key, members, _doubts(members))
        for key, members in sorted(by_key.items())
        if len(members) > 1
    ]


def pending_groups():
    """Doubtful groups the owner hasn't decided on yet."""
    return [
        g for g in name_groups()
        if g.doubts and g.key not in CONFIRMED_GROUPS and g.key not in REJECTED_GROUPS
    ]  # fmt: skip


class _UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        self.parent[self.find(a)] = self.find(b)


@dataclass
class GroupingReport:
    families: int = 0
    exercises: int = 0
    created: int = 0
    pending: list = field(default_factory=list)
    missing: list = field(default_factory=list)  # names in MANUAL_GROUPS not in the library


@transaction.atomic
def group_movements():
    """Put built-in exercises into families. Idempotent; never touches history.

    Families that users already joined (their own variants) are kept and merged, never
    emptied: when two families become one, every member moves to the surviving one.
    """
    builtins = {e.pk: e for e in Exercise.objects.filter(owner=None)}
    by_name = {e.name: e for e in builtins.values()}
    links = _UnionFind()

    for name, base_name, *_ in SMITH_VARIANTS:
        if base_name and name in by_name and base_name in by_name:
            links.union(by_name[name].pk, by_name[base_name].pk)
    missing = []
    for names in MANUAL_GROUPS.values():
        found = [by_name[n].pk for n in names if n in by_name]
        missing += [n for n in names if n not in by_name]
        for pk in found[1:]:
            links.union(found[0], pk)
    manual_names = {frozenset(names): family_name for family_name, names in MANUAL_GROUPS.items()}
    for group in name_groups(sorted(builtins.values(), key=lambda e: e.name)):
        if group.key in REJECTED_GROUPS:
            continue
        if group.doubts and group.key not in CONFIRMED_GROUPS:
            continue
        first, *rest = group.exercises
        for other in rest:
            links.union(first.pk, other.pk)

    components = defaultdict(list)
    for pk in list(links.parent):
        components[links.find(pk)].append(builtins[pk])

    report = GroupingReport(missing=missing)
    for members in components.values():
        if len(members) < 2:
            continue
        movement_ids = sorted({e.movement_id for e in members if e.movement_id})
        if movement_ids:
            target = Movement.objects.get(pk=movement_ids[0])
            if target.owner_id is not None:  # a built-in family must be built-in
                target.owner = None
                target.save(update_fields=["owner"])
        else:
            plainest = min(members, key=lambda e: len(movement_name(e.name)))
            name = manual_names.get(
                frozenset(e.name for e in members), movement_name(plainest.name)
            )
            target = Movement.objects.create(name=name)
            report.created += 1
        # Members, plus users' variants that were in a family being merged away.
        Exercise.objects.filter(pk__in=[e.pk for e in members]).update(movement=target)
        if len(movement_ids) > 1:
            Exercise.objects.filter(movement_id__in=movement_ids[1:]).update(movement=target)
            Movement.objects.filter(pk__in=movement_ids[1:]).delete()
        report.families += 1
        report.exercises += len(members)
    report.pending = pending_groups()
    return report
