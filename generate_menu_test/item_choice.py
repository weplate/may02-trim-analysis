import itertools
import time

from common import BUILD_MUSCLE, LOSE_WEIGHT, ATHLETIC_PERFORMANCE, IMPROVE_TONE, IMPROVE_HEALTH, PROTEIN, GRAINS, \
    VEGETABLE
from portion import SimulatedAnnealing, PlateSectionState, MealItemSpec
from requirements import nutritional_info_for, StudentProfileSpec


class PlateSection:
    LARGE = 'large'
    SMALL1 = 'small1'
    SMALL2 = 'small2'

    @classmethod
    def all(cls):
        return [cls.LARGE, cls.SMALL1, cls.SMALL2]


# https://www.notion.so/weplate/Mathematical-Calculations-f561b494f2444cfc87023ef615cf2bea#c137e967c1224678be2079cb5a55a3a6
# Which section (protein, veg, carb) should have the large portion
LARGE_PORTION = {
    BUILD_MUSCLE: PROTEIN,
    ATHLETIC_PERFORMANCE: GRAINS,
    LOSE_WEIGHT: VEGETABLE,
    IMPROVE_TONE: PROTEIN,
    IMPROVE_HEALTH: VEGETABLE,
}

# How many items to pick
CHOOSE_COUNT = 3


class MealItemSelector:
    def __init__(self, profile: StudentProfileSpec, items: list[MealItemSpec],
                 large_portion_max: float, small_portion_max: float,
                 coefficients: tuple[float], sa_alpha: float, sa_lo: float, seed: int):
        """
        Creates a MealItemSelector object, which runs the algorithm that selects the best item choices given a list of
        meal items.
        @param profile: An object that contains the correct biological/health properties of the student to choose for
        @param items: A list of MealItemSpec, which represent the list of meal items available at the meal
        @param large_portion_max: Size of the large plate section (mL)
        @param small_portion_max: Size of the small plate sections (mL)
        @param coefficients: List of weights denoting how much each nutrient is weighted.  The cost of a state is
        determined by the distance of its nutrition facts to the 'allowed' range.  Euclidian distance**2 is the metric
        used to measure how far each nutrient is from its goal.  These are then scaled by the individual coefficients.
        See SimulatedAnnealing.cost_of for more details on which coefficient affects what.
        @param sa_alpha: Alpha for simulated annealing runs
        @param sa_lo: Minimum temperature for simulated annealing runs
        @param seed: RNG seed for simulated annealing runs
        """
        self.profile = profile
        self.items = items

        self.coefficients = coefficients
        self.sa_alpha = sa_alpha
        self.sa_lo = sa_lo
        self.seed = seed
        self.large_portion_max = large_portion_max
        self.small_portion_max = small_portion_max

        self.requirements = nutritional_info_for(profile)
        self._result_obj = {}
        self.result_cost = -1
        self.runtime = -1
        self.done = False

    def run_algorithm(self):
        large_category = PROTEIN
        small1_category = VEGETABLE
        small2_category = GRAINS

        large_items = [item for item in self.items if item.category == PROTEIN]
        small1_items = [item for item in self.items if item.category == VEGETABLE]
        small2_items = [item for item in self.items if item.category == GRAINS]

        large_portion = LARGE_PORTION[self.profile.health_goal]
        # TODO: remove later, temporary workaround to allow for 2 sections for testing breakfast
        if self.large_portion_max == 0:
            large_portion = PROTEIN

        if large_portion == VEGETABLE:
            large_items, small1_items = small1_items, large_items
            large_category, small1_category = small1_category, large_category
        elif large_portion == GRAINS:
            large_items, small2_items = small2_items, large_items
            large_category, small2_category = small2_category, large_category

        cost_cache = {}
        start_time = time.perf_counter()

        def cache_id(item_1, item_2, item_3):
            return f'{item_1.id}-{item_2.id}-{item_3.id}'

        for item_l, item_s1, item_s2 in itertools.product(large_items, small1_items, small2_items):
            sa = SimulatedAnnealing(profile=self.profile,
                                    state=[PlateSectionState.from_item_spec(item, volume, 1, 'who cares')
                                           for item, volume in zip((item_l, item_s1, item_s2), (
                                        self.large_portion_max, self.small_portion_max, self.small_portion_max))],
                                    coefficients=self.coefficients,
                                    alpha=self.sa_alpha,
                                    smallest_temp=self.sa_lo,
                                    seed=self.seed)
            sa.run_algorithm()
            cost_cache[cache_id(item_l, item_s1, item_s2)] = sa.final_cost

        best = [], [], []
        best_cost = sum(cost_cache.values()) + 1
        for comb_l, comb_s1, comb_s2 in itertools.product(
                itertools.combinations(large_items, min(CHOOSE_COUNT, len(large_items))),
                itertools.combinations(small1_items, min(CHOOSE_COUNT, len(small1_items))),
                itertools.combinations(small2_items, min(CHOOSE_COUNT, len(small2_items)))
        ):
            l1 = list(comb_l)
            l2 = list(comb_s1)
            l3 = list(comb_s2)
            cur_cost = 0
            for x, y, z in itertools.product(l1, l2, l3):
                cur_cost += cost_cache[cache_id(x, y, z)]

            if cur_cost < best_cost:
                best_cost = cur_cost
                best = (l1, l2, l3)

        def to_id_list(items):
            return [item.id for item in items]

        l1, l2, l3 = best
        self._result_obj = {
            PlateSection.LARGE: {
                'items': to_id_list(l1),
                'category': large_category
            },
            PlateSection.SMALL1: {
                'items': to_id_list(l2),
                'category': small1_category
            },
            PlateSection.SMALL2: {
                'items': to_id_list(l3),
                'category': small2_category
            },
        }
        self.result_cost = best_cost
        self.runtime = time.perf_counter() - start_time
        self.done = True

    def result_obj(self):
        return self._result_obj
