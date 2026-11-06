"""The owner's decisions on doubtful movement families (see exercises/movements.py).

A family is doubtful when its members share equipment, work different muscle groups,
belong to different categories or differ in one side vs both sides. Such a group is
applied only after its key is listed in CONFIRMED_GROUPS. Keys in REJECTED_GROUPS are
never grouped (also usable for clear groups that turn out wrong).

`python manage.py group_movements --pending` lists the groups still waiting.
"""

CONFIRMED_GROUPS: set[str] = set()

REJECTED_GROUPS: set[str] = set()
