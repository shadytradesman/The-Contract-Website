from django.db import migrations, models
from django.utils.timezone import now

KS_REWARDS = \
"""Professional,https://thecontractrpg.com/profile/view/1766/,0,0,0,0,7,0,0,0
Veteran,https://www.thecontractrpg.com/profile/view/1029/,0,0,0,0,0,17,0,0
Professional,https://www.thecontractrpg.com/profile/view/9/,0,0,0,0,7,0,0,0
Veteran,https://www.thecontractrpg.com/profile/view/169/,0,0,0,0,0,17,0,0
Novice,https://thecontractrpg.com/profile/view/2084/,0,0,0,4,0,0,0,0
Veteran,https://thecontractrpg.com/profile/view/1131/,0,0,0,0,0,17,0,0
Seasoned,thecontractrpg.com/profile/view/63/,0,0,0,4,0,0,0,0
Professional,https://thecontractrpg.com/profile/view/116/,0,0,0,0,7,0,0,0
Seasoned,https://www.thecontractrpg.com/profile/view/1787/,0,0,0,4,0,0,0,0
Harbinger,https://thecontractrpg.com/profile/view/694/,0,0,0,0,0,0,27,0
Harbinger,https://www.thecontractrpg.com/profile/view/11/,0,0,0,0,0,0,27,0
Newbie,https://thecontractrpg.com/profile/view/170/,0,0,2,0,0,0,0,0
Veteran,https://thecontractrpg.com/profile/view/175/,0,0,0,0,0,17,0,0
Seasoned,https://thecontractrpg.com/profile/view/2056/,0,0,0,4,0,0,0,0
Novice,https://www.thecontractrpg.com/profile/view/2118/,0,0,0,4,0,0,0,0
Professional,https://thecontractrpg.com/profile/view/2122/,0,0,0,0,7,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2064/,0,0,0,4,0,0,0,0
Veteran,https://thecontractrpg.com/profile/view/976/,0,0,0,0,0,17,0,0
Professional,https://thecontractrpg.com/profile/view/2100/,0,0,0,0,7,0,0,0
Seasoned,https://www.thecontractrpg.com/profile/view/397/,0,0,0,4,0,0,0,0
Powers That Be,https://thecontractrpg.com/profile/view/770/,0,0,0,0,0,0,0,9999999
Professional,https://thecontractrpg.com/profile/view/1446/,0,0,0,0,7,0,0,0
Novice,https://thecontractrpg.com/profile/view/2058/,0,0,0,4,0,0,0,0
Powers That Be,https://www.thecontractrpg.com/profile/view/552/,0,0,0,0,0,0,0,9999999
Seasoned,https://thecontractrpg.com/profile/view/839/,0,0,0,4,0,0,0,0
Veteran,https://thecontractrpg.com/profile/view/816/,0,0,0,0,0,17,0,0
Seasoned,https://thecontractrpg.com/profile/view/1785/,1,0,0,4,0,0,0,0
Veteran,https://www.thecontractrpg.com/profile/view/273/,0,0,0,0,0,17,0,0
Seasoned,https://thecontractrpg.com/profile/view/1030/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/272/,0,0,0,4,0,0,0,0
Harbinger,https://www.thecontractrpg.com/profile/view/570/,0,0,0,0,0,0,27,0
Newbie,https://thecontractrpg.com/profile/view/2063/,0,0,2,0,0,0,0,0
Newbie,https://thecontractrpg.com/profile/view/2128/,0,0,2,0,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2087/,0,0,0,4,0,0,0,0
Veteran,https://thecontractrpg.com/profile/view/206/,0,0,0,0,0,17,0,0
Veteran,https://thecontractrpg.com/profile/view/926/,0,0,0,0,0,17,0,0
Newbie,https://www.thecontractrpg.com/profile/view/455/,0,0,2,0,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/1987/,0,0,0,4,0,0,0,0
Professional,https://www.thecontractrpg.com/profile/view/1806/,0,0,0,0,7,0,0,0
Newbie,https://www.thecontractrpg.com/profile/view/1799/,0,0,2,0,0,0,0,0
Harbinger,https://www.thecontractrpg.com/profile/view/99/,0,0,0,0,0,0,27,0
Seasoned,https://www.thecontractrpg.com/profile/view/2054/,0,0,0,4,0,0,0,0
Seasoned,https://www.thecontractrpg.com/profile/view/1032/,0,0,0,4,0,0,0,0
Veteran,https://thecontractrpg.com/profile/view/728/,0,0,0,0,0,17,0,0
Seasoned,https://thecontractrpg.com/profile/view/2070/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/1826/,0,0,0,4,0,0,0,0
Newbie,https://thecontractrpg.com/profile/view/729/,0,0,2,0,0,0,0,0
Newbie,https://thecontractrpg.com/profile/view/21/,0,0,2,0,0,0,0,0
Newbie,https://www.thecontractrpg.com/profile/view/1888/,0,0,2,0,0,0,0,0
Professional,https://thecontractrpg.com/profile/view/1821/,0,0,0,0,7,0,0,0
Newbie,https://www.thecontractrpg.com/profile/view/1835/,0,0,2,0,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2119/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2086/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/1829/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/1024/,0,0,0,4,0,0,0,0
Novice,https://www.thecontractrpg.com/profile/view/1893/,0,0,0,4,0,0,0,0
Seasoned,https://www.thecontractrpg.com/profile/view/2076/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2089/,0,0,0,4,0,0,0,0
Novice,https://www.thecontractrpg.com/profile/view/1722/,0,0,0,4,0,0,0,0
Newbie,https://thecontractrpg.com/profile/view/1524/,0,0,2,0,0,0,0,0
Novice,https://thecontractrpg.com/profile/view/2096/,0,0,0,4,0,0,0,0
Newbie,https://thecontractrpg.com/profile/view/1833/,0,0,2,0,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/1805/,0,0,0,4,0,0,0,0
Newbie,https://thecontractrpg.com/profile/view/1870/,0,0,2,0,0,0,0,0
Novice,https://thecontractrpg.com/profile/view/1819/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2091/,0,0,0,4,0,0,0,0
Newbie,https://thecontractrpg.com/profile/view/2068/,0,0,2,0,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/1531/,0,0,0,4,0,0,0,0
Seasoned,https://www.thecontractrpg.com/profile/view/1929/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2062/,0,0,0,4,0,0,0,0
Professional,https://www.thecontractrpg.com/profile/view/620/,0,0,0,0,7,0,0,0
Seasoned,https://www.thecontractrpg.com/profile/view/1858/,0,0,0,4,0,0,0,0
Novice,https://thecontractrpg.com/profile/view/2055/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2073/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2060/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2071/,0,0,0,4,0,0,0,0
Novice,https://thecontractrpg.com/profile/view/2059/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/1990/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2074/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2069/,0,0,0,4,0,0,0,0
Novice,https://www.thecontractrpg.com/profile/view/1989/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2114/,0,0,0,4,0,0,0,0
Seasoned,thecontractrpg.com/profile/view/2057/,0,0,0,4,0,0,0,0
Newbie,https://www.thecontractrpg.com/profile/view/1985/,0,0,2,0,0,0,0,0
Newbie,https://thecontractrpg.com/profile/view/1986/,0,0,2,0,0,0,0,0
Professional,https://thecontractrpg.com/profile/view/1941/,0,0,0,0,7,0,0,0
Newbie,https://thecontractrpg.com/profile/view/53/,0,0,2,0,0,0,0,0
Newbie,https://thecontractrpg.com/profile/view/2065/,0,0,2,0,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/1442/,0,0,0,4,0,0,0,0
Newbie,Thecontractrpg.com/profile/view/1606/,0,10,2,0,0,0,0,0
Novice,https://thecontractrpg.com/profile/view/287/,0,0,0,4,0,0,0,0
Newbie,https://thecontractrpg.com/profile/view/779/,1,0,2,0,0,0,0,0
Newbie,https://www.thecontractrpg.com/profile/view/1894/,0,0,2,0,0,0,0,0
Newbie,https://www.thecontractrpg.com/profile/view/1880/,0,0,2,0,0,0,0,0
Seasoned,https://www.thecontractrpg.com/profile/view/2105/,0,0,0,4,0,0,0,0
Newbie,https://www.thecontractrpg.com/profile/view/1885/,0,0,2,0,0,0,0,0
Professional,https://www.thecontractrpg.com/profile/view/214/,0,0,0,0,7,0,0,0
Seasoned,https://www.thecontractrpg.com/profile/view/2061/,0,0,0,4,0,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/2131/,0,0,0,4,0,0,0,0
Seasoned,https://www.thecontractrpg.com/profile/view/695/,0,0,0,4,0,0,0,0
Professional,https://thecontractrpg.com/profile/view/339/,0,0,0,0,7,0,0,0
Seasoned,https://thecontractrpg.com/profile/view/1982/,0,0,0,4,0,0,0,0
Novice,https://thecontractrpg.com/profile/view/2120/,0,0,0,4,0,0,0,0
Newbie,https://www.thecontractrpg.com/profile/view/1905/,0,0,2,0,0,0,0,0
Seasoned,https://www.thecontractrpg.com/profile/view/594/,0,0,0,4,0,0,0,0
Newbie,https://thecontractrpg.com/profile/view/2121/,0,0,2,0,0,0,0,0
Veteran,https://www.thecontractrpg.com/profile/view/18/,0,0,0,0,0,17,0,0
Novice,https://thecontractrpg.com/profile/view/2098/,0,0,0,4,0,0,0,0 """

KICKSTARTER_NONE = 'KS_NONE'
KICKSTARTER_NEWBIE = 'KS_NEWBIE'
KICKSTARTER_NOVICE = 'KS_NOVICE'
KICKSTARTER_SEASONED = 'KS_SEASONED'
KICKSTARTER_PROFESSIONAL = 'KS_PROFESSIONAL'
KICKSTARTER_VETERAN = 'KS_VETERAN'
KICKSTARTER_HARBINGER = 'KS_HARBINGER'
KICKSTARTER_POWERS = 'KS_POWERS'
KS_REWARD_LEVEL = {
    'Newbie': KICKSTARTER_NEWBIE,
    'Novice': KICKSTARTER_NOVICE,
    'Seasoned': KICKSTARTER_SEASONED,
    'Professional': KICKSTARTER_PROFESSIONAL,
    'Veteran': KICKSTARTER_VETERAN,
    'Harbinger': KICKSTARTER_HARBINGER,
    'Powers That Be': KICKSTARTER_POWERS,
}

REWARD_TITLES = "Add-on 1 Exchange Scenario,Add-on 10 Exchange Scenarios,2 Exchange Scenarios,4 Exchange Scenarios,7 Exchange Scenarios,17 Exchange Scenarios,27 Exchange Scenarios,Unlimited Exchange Credits"

def migrate_ks_rewards(apps, schema_editor):
    Profile = apps.get_model('profiles', 'Profile')
    ExchangeCreditChange = apps.get_model('games', 'ExchangeCreditChange')
    lines = KS_REWARDS.split('\n')
    reward_titles = REWARD_TITLES.split(',')
    for line in lines:
        cells = line.split(',')
        profile_num = [x for x in cells[1].split('/') if x][-1]
        print("processing", profile_num, cells)
        profile = Profile.objects.get(pk=profile_num)
        reward_tier = cells[0]
        profile.ks_reward_level = KS_REWARD_LEVEL[reward_tier]
        for idx, cell in enumerate(cells[2:]):
            if int(cell) > 0:
                credit_count = int(cell) * 100
                ExchangeCreditChange.objects.create(rewarded_player=profile.user,
                                                    reason=reward_titles[idx],
                                                    value=credit_count)
                profile.exchange_credits += credit_count
        profile.save()


def reverse_migrate_primary_writeup():
    pass


class Migration(migrations.Migration):

    dependencies = [
         ('games', '0066_manual_exchange_credits_record'),
         ('profiles', '0032_profile_ks_reward_level'),
    ]

    operations = [
        migrations.RunPython(migrate_ks_rewards, reverse_migrate_primary_writeup),
    ]
