from django.db import migrations


def seed(apps, schema_editor):
    from tien.seed import INSTITUTIONS, PROGRAMS
    Institution = apps.get_model("tien", "Institution")
    Program = apps.get_model("tien", "Program")
    for name, short, itype, cat, region, city, lat, lon, wave in INSTITUTIONS:
        Institution.objects.update_or_create(name=name, defaults=dict(
            short_name=short, institution_type=itype, map_category=cat, region=region, city=city,
            latitude=lat, longitude=lon, rollout_wave=wave, coordinates_estimated=wave is None))
    for slug, kind, title, icon, summary, who, fmt, benefits, role, order in PROGRAMS:
        Program.objects.update_or_create(slug=slug, defaults=dict(
            kind=kind, title=title, icon=icon, summary=summary, who=who, format=fmt, benefits=benefits,
            join_role=role, order=order))


class Migration(migrations.Migration):
    dependencies = [("tien", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
