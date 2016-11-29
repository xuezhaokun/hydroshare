# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models


def remove_extra_privileges(apps, schema_editor):
    """ 
    Remove extra records from privileges tables
        
    This change removes extra records that were generated by early versions of the user interface. 
    These records are redundant, in the sense that the highest privilege always wins. 
    The method for eliminating them is to retain the highest privilege that was instituted latest. 
    This is consistent with what would have resulted if the access control system were running 
    under the new semantics. 

    For example, if user 'foo' had the following privilege records over resource 'bar': 
    
    
        VIEW   1/1/2016  michael 
        CHANGE 1/2/2016  robert
        VIEW   2/1/2016  alva

    Then 
    
    * The new effective privilege record will be: 
        
        CHANGE 1/2/2016  robert

    * The first record will be considered to be overridden by the second. 
    * The third record cannot be honored because it would result in a perceivable downgrade of 
      privilege. So it is ignored. 

    There are commented out print statements that will track the progress of this request if enabled. 
    These do not show up in my (broken) development system. 

    """
    User = apps.get_model("auth", "User")
    Group = apps.get_model("auth", "Group")
    BaseResource = apps.get_model("hs_core", "BaseResource")
    UserResourcePrivilege = apps.get_model("hs_access_control", "UserResourcePrivilege")
    UserGroupPrivilege = apps.get_model("hs_access_control", "UserGroupPrivilege")
    GroupResourcePrivilege = apps.get_model("hs_access_control", "GroupResourcePrivilege")

    # brute force removal of offending records.
    for u in User.objects.all():
        for r in BaseResource.objects.all():
            records = UserResourcePrivilege.objects.filter(user=u, resource=r)
            if records.count() > 1:  # do nothing if there are no duplicates
                # print(str.format("User '{}' (id={}) has {} privilege records" +
                #                  " over resource '{}'",
                #                  str(r.user.username).encode('ascii'), str(r.user.id),
                #                  str(records.count()),
                #                  str(r.short_id).encode('ascii')))

                # for x in records:
                #     print(str.format("   {}", str(x)))

                # determine the lowest privilege number
                min = records.aggregate(models.Min('privilege'))
                min_privilege = min['privilege__min']
                # print (str.format("   minimum privilege is {}", str(min_privilege)))

                # of records with this number, select the record with maximum timestamp.
                # This determines the (last) grantor
                max = records.filter(privilege=min_privilege).aggregate(models.Max('start'))
                max_start = max['start__max']
                # print (str.format("   maximum start is {}", str(max_start)))

                to_keep = records.filter(privilege=min_privilege, start=max_start)
                if to_keep.count() == 1:
                    # print("   one UNIQUE start record: {}", str(to_keep[0]))
                    to_delete = records.exclude(pk__in=to_keep)
                    to_delete.delete()
                elif to_keep.count() > 1:  # unlikely
                    kept = records[0]  # choose first one arbitrarily
                    # print("   choosing arbitrary record: {}", str(kept))
                    to_delete = records.exclude(pk=kept)
                    to_delete.delete()

    for u in User.objects.all():
        for g in Group.objects.all():

            records = UserGroupPrivilege.objects.filter(user=u, group=g)
            if records.count() > 1:  # do nothing if there are no duplicates
                # print(str.format("User '{}' (id={}) has {} privilege records" +
                #                  " over group '{}' ({})",
                #                  str(r.user.username), str(r.user.id),
                #                  str(records.count()),
                #                  str(r.group.name), str(r.group.id)))

                # determine the lowest privilege number
                min = records.aggregate(models.Min('privilege'))
                min_privilege = min['privilege__min']
                # print (str.format("   minimum privilege is {}", str(min_privilege)))

                # of records with this number, select the record with maximum timestamp.
                # This determines the (last) grantor
                max = records.filter(privilege=min_privilege).aggregate(models.Max('start'))
                max_start = max['start__max']
                # print (str.format("   maximum start is {}", str(max_start)))

                to_keep = records.filter(privilege=min_privilege, start=max_start)
                if to_keep.count() == 1:
                    # print("   one UNIQUE start record: {}", str(to_keep[0]))
                    to_delete = records.exclude(pk__in=to_keep)
                    to_delete.delete()

                elif to_keep.count() > 1:  # unlikely
                    kept = records[0]  # choose first one arbitrarily
                    # print("   choosing arbitrary record: {}", str(kept))
                    to_delete = records.exclude(pk=kept)
                    to_delete.delete()

    for g in Group.objects.all():
        for r in BaseResource.objects.all():
            records = GroupResourcePrivilege.objects.filter(group=g, resource=r)
            if records.count() > 1:  # do nothing if there are no duplicates
                # print(str.format("Group '{}' (id={}) has {} privilege records" +
                #                  " over resource '{}'",
                #                  str(r.group.name).encode('ascii'), str(r.group.id),
                #                  str(records.count()),
                #                  str(r.short_id)).encode('ascii'))

                # determine the lowest privilege number
                min = records.aggregate(models.Min('privilege'))
                min_privilege = min['privilege__min']
                # print (str.format("   minimum privilege is {}", str(min_privilege)))

                # of records with this number, select the record with maximum timestamp.
                # This determines the (last) grantor
                max = records.filter(privilege=min_privilege).aggregate(models.Max('start'))
                max_start = max['start__max']
                # print (str.format("   maximum start is {}", str(max_start)))

                to_keep = records.filter(privilege=min_privilege, start=max_start)
                if to_keep.count() == 1:
                    # print("   one UNIQUE start record: {}", str(to_keep[0]))
                    to_delete = records.exclude(pk__in=to_keep)
                    to_delete.delete()

                elif to_keep.count() > 1:  # unlikely
                    kept = records[0]  # choose first one arbitrarily
                    # print("   choosing arbitrary record: {}", str(kept))
                    to_delete = records.exclude(pk=kept)
                    to_delete.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0014_auto_20160424_1628'),
    ]

    operations = [
        migrations.RunPython(remove_extra_privileges),
    ]