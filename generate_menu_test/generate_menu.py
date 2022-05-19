from portion import MealItemSpec, PlateSectionState, DEFAULT_COEFFICIENTS
from requirements import StudentProfileSpec
from dataclasses import fields
from item_choice import LARGE_PORTION
from random import *
from alive_progress import alive_bar
import csv
import os
import json

NUM_TRIALS = 10000

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

with open('...something') as f:
    profile = StudentProfileSpec(whatever)

def filter_category(category):
    return lambda x: x.category == category

large = list(map(filter_category('protein'), items))
small1 = list(map(filter_category('grain'), items))
small2 = list(map(filter_category('vegetable'), items))

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

    return cache[key] := sim.final_cost

print(f'Large count: {len(large)}, small1 count: {len(small1)}, small2 count: {len(small2)}')

def all_cost(a, b, c):
    tot = 0
    for x in a:
        for y in b:
            for z in c:
                tot += get_cost(x, y, z)
    return tot

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
        best_cost = -1

        with alive_bar(NUM_TRIALS) as bar:
            cat_num = randint(0, 2)
            item_num = randint(0, 2)
except KeyboardInterrupt:
    print(f'Exiting... writing results')
    with open('results.json', 'w') as f:
        json.dump(l, f)
