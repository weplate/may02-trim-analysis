from portion import MealItemSpec, PlateSectionState, DEFAULT_COEFFICIENTS, SimulatedAnnealing
from requirements import StudentProfileSpec
from dataclasses import fields
from item_choice import LARGE_PORTION
from random import *
from alive_progress import alive_bar
import datetime
import csv
import os
import json

NUM_TRIALS = 10000

# load items
def mealitemspec_from_dict(d):
    dd = {'id': d['pk']}
    for field in fields(MealItemSpec):
        if field.name in d:
            dd[field.name] = d[field.name]
    return MealItemSpec(**dd)

with open('../nutrition_table.csv') as f:
    items_dict = csv.DictReader(f)
    items = list(map(mealitemspec_from_dict, items_dict))

print(f'got {len(items)} items')

# load person
with open('fake_person.json') as f:
    obj = json.load(f)
    profile = StudentProfileSpec(
            height=obj['Height'],
            weight=obj['Weight'],
            birthdate=datetime.date.fromisoformat(obj['Birthdate']),
            meals=[],
            meal_length=0,
            sex=obj['Sex'],
            health_goal=obj['Health_Goal'],
            activity_level=obj['Activity_Level']
    )

def filter_category(category):
    return lambda x: x.category == category

large = list(filter(filter_category('protein'), items))
small1 = list(filter(filter_category('grain'), items))
small2 = list(filter(filter_category('vegetable'), items))

large_cat = LARGE_PORTION[profile.health_goal]
if large_cat == 'vegetable':
    small2, large = large, small2
elif large_cat == 'grain':
    small1, large = large, small1

cache = {}
def get_cost(item1, item2, item3):
    key = f'{item1.id}_{item2.id}_{item3.id}'

    if key in cache:
        return cache[key]

    sim = SimulatedAnnealing(profile, \
            [PlateSectionState.from_item_spec(item, volume, 1, name) for \
            item, volume, name in zip((item1, item2, item3), (610, 270, 270), ('large', 'small1', 'small2'))], \
            DEFAULT_COEFFICIENTS, \
            0.99, \
            0.01, \
            20210226)

    sim.run_algorithm()

    cache[key] = sim.final_cost
    return sim.final_cost

print(f'Large count: {len(large)}, small1 count: {len(small1)}, small2 count: {len(small2)}')

def all_cost(a, b, c):
    tot = 0
    for x in a:
        for y in b:
            for z in c:
                tot += get_cost(x, y, z)
    return tot

def map_names(items):
    return list(map(lambda x: x.name, items))

l = []
if os.path.exists('results.json'):
    with open('results.json') as f:
        print('Loading previous results')
        l = json.load(f)

try:
    while 1:
        large_ans = sample(large, k=3)
        small1_ans = sample(small1, k=3)
        small2_ans = sample(small2, k=3)

        num_best = 0
        best_cost = all_cost(large_ans, small1_ans, small2_ans)

        with alive_bar(NUM_TRIALS) as bar:
            for _ in range(NUM_TRIALS):
                cat_num = randint(0, 2)
                item_num = randint(0, 2)

                l_pool = (large, small1, small2)[cat_num]
                l_item = (large_ans, small1_ans, small2_ans)[cat_num]

                new_item = choice(l_pool)
                old_item = l_item[item_num]

                l_item[item_num] = new_item
                new_cost = all_cost(large_ans, small1_ans, small2_ans)

                if best_cost == -1 or new_cost < best_cost:
                    num_best += 1
                    best_cost = new_cost
                    l.append({
                        'large': large_ans.copy(),
                        'small1': small1_ans.copy(),
                        'small2': small2_ans.copy(),
                        'cost': best_cost,
                    })

                    bar.text = f'cost={best_cost}\nlarge={map_names(large_ans)}\nsmall1={map_names(small1_ans)}\nsmall2={map_names(small2_ans)}'
                else:
                    l_item[item_num] = old_item

                bar()
except KeyboardInterrupt:
    print(f'Exiting... writing results')
    with open('results.json', 'w') as f:
        json.dump(l, f)
