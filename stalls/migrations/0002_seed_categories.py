from django.db import migrations

CATEGORIES = [
    ("Crab", "Blue crab, mud crab and other crabs"),
    ("Tuna", "Yellowfin and skipjack tuna"),
    ("Squid", "Fresh squid (pusit)"),
    ("Shrimp", "Prawns and shrimp"),
    ("Scallops", "Fresh scallops"),
    ("Lobster", "Spiny lobster"),
    ("Octopus", "Fresh octopus (nukos)"),
    ("Milkfish", "Bangus"),
    ("Tilapia", "Freshwater and brackish tilapia"),
    ("Mackerel", "Galunggong and other mackerel scad"),
    ("Grouper", "Lapu-lapu and other groupers"),
    ("Seaweed", "Fresh seaweed (guso)"),
]


def seed(apps, schema_editor):
    Category = apps.get_model("stalls", "SeafoodCategory")
    for name, description in CATEGORIES:
        Category.objects.get_or_create(name=name, defaults={"description": description})


def unseed(apps, schema_editor):
    apps.get_model("stalls", "SeafoodCategory").objects.filter(
        name__in=[c[0] for c in CATEGORIES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("stalls", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
