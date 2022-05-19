import dataclasses
import math
import random
import time
from dataclasses import dataclass
from math import exp
from typing import Union

from common import Nutrition
from requirements import nutritional_info_for, StudentProfileSpec


@dataclass
class MealItemSpec:
    id: int
    category: str
    cafeteria_id: str
    portion_volume: float
    max_pieces: int

    calories: float = 0.
    carbohydrate: float = 0.
    protein: float = 0.
    total_fat: float = 0.
    saturated_fat: float = 0.
    trans_fat: float = 0.

    sugar: float = 0.
    cholesterol: float = 0.
    fiber: float = 0.

    sodium: float = 0.
    potassium: float = 0.
    calcium: float = 0.
    iron: float = 0.

    vitamin_a: float = 0.
    vitamin_c: float = 0.
    vitamin_d: float = 0.


def clamp(x: float, a: float, b: float) -> float:
    """
    Clamps a value x within the range [a, b]

    @param x: Value to clamp
    @param a: Lower bound
    @param b: Upper bound
    @return:
    """

    if x < a:
        return a
    elif x > b:
        return b
    return x


def dist_sq(x: float, l: float, r: float) -> float:
    """
    Returns smallest distance (squared) from x to any number in the range [l, r]

    @param x: Point to check distance of (on the number line)
    @param l: Lower bound of the range
    @param r: Upper bound of the range
    @return:
    """
    if x < l:
        return (l - x) ** 2
    elif r < x:
        return (x - r) ** 2
    return 0


def random_sign() -> int:
    """
    Randomly returns -1 or 1
    @return:
    """
    return 1 - 2 * random.randint(0, 1)  # random sign


def ceil_div(a: int, b: int) -> int:
    """
    Given non-negative integers, returns ceil(a / b)

    @param a: self-explanatory
    @param b: self-explanatory
    @return:
    """
    return (a + b - 1) // b


@dataclass
class PlateSectionState:
    nutrition: Nutrition
    portion_volume: Union[float, int]
    discrete: bool
    max_volume: Union[float, int]
    volume: Union[float, int] = 0
    section_name: str = ''
    id: Union[str, int] = ''  # We allow either pk (int) or cafeteria_id (str)

    @classmethod
    def from_item_spec(cls, item: MealItemSpec, container_volume: float, num_sections: int, section_name: str):
        """
        Creates a PlateSectionState (with 0 cur. volume) from a given meal item (as MealItemSpec) and other parameters
        @param item The meal item to create the object from
        @param container_volume The total container volume, in DB format (i.e. positive for continuous, negative integer for discrete)
        @param num_sections The number of sections this container is divided into (so the actual volume can be computed by how much of the section this occupies)
        @param section_name The name of the section (currently, "large", "small1", or "small2")
        @return A PlateSectionState object
        """
        discrete = item.portion_volume < 0
        if discrete:
            volume = 0
            portion_volume = -item.portion_volume
            max_volume = ceil_div(item.max_pieces, num_sections)
        else:
            volume = 0.
            portion_volume = item.portion_volume
            max_volume = container_volume / num_sections

        return PlateSectionState(nutrition=Nutrition.from_object(item),
                                 portion_volume=portion_volume,
                                 discrete=discrete,
                                 max_volume=max_volume,
                                 volume=volume,
                                 section_name=section_name,
                                 id=item.id)

    @property
    def min_volume(self):
        """
        @return: Returns the min volume instead of the max volume
        """
        return max(1, ceil_div(self.max_volume, 2)) if self.discrete else self.max_volume / 2

    def scaled_nutrition(self):
        """
        @return: Returns the nutrition facts scaled by the portion volume
        """
        return self.nutrition * (self.volume / self.portion_volume)

    def format_volume(self):
        """
        @return: Returns the volume of the item but formatted properly (i.e. discrete volumes are negative
        """
        return self.volume if not self.discrete else float(-self.volume)

    def format_max_volume(self):
        """
        @return: Returns the volume of the item but formatted properly (i.e. discrete volumes will be formatted as negative floats)
        """
        return self.max_volume if not self.discrete else float(-self.max_volume)

    def as_dict(self):
        """
        Convert fields to dict
        @return: dict with the fields
        """
        return dataclasses.asdict(self)

    def copy(self):
        """
        @return: Creates a copy, nutrition facts are cloned recursively
        """
        return PlateSectionState(nutrition=self.nutrition.copy(),
                                 volume=self.volume,
                                 portion_volume=self.portion_volume,
                                 max_volume=self.max_volume,
                                 section_name=self.section_name,
                                 discrete=self.discrete,
                                 id=self.id)

    def with_min_volume(self):
        """
        Clones the state but with the min-volume.
        """
        ret = self.copy()
        ret.volume = ret.min_volume
        return ret

    def with_max_volume(self):
        """
        Clones the state but with the max-volume.
        """
        ret = self.copy()
        ret.volume = ret.max_volume
        return ret

    def with_mid_volume(self):
        """
        Clones the state but with the mid-volume.
        """
        ret = self.copy()
        if ret.discrete:
            ret.volume = ceil_div(3 * ret.max_volume, 4)
        else:
            ret.volume = 0.75 * ret.max_volume
        return ret

    def nudge(self, ratio):
        """
        Updates the volume based on some fraction/ratio of the max volume, making sure to clamp at max/min values, and
        dealing with special cases with discrete values
        @param ratio Ratio to nudge the volume by
        @return: The old volume, pre-nudge
        """
        old_volume = self.volume
        if self.discrete:
            abs_change = int(math.ceil(abs(ratio) * self.max_volume))
            self.volume = clamp(self.volume + abs_change * int((ratio > 0) - (ratio < 0)), self.min_volume,
                                self.max_volume)
        else:
            self.volume = clamp(self.volume + ratio * self.max_volume, self.min_volume, self.max_volume)
        return old_volume


def nutrition_of(state: list[PlateSectionState]):
    """
    Given a list of PlateSectionStates, sums the scaled nutrition facts over the states
    @param state:
    @return: The summed nutrition facts over all states
    """
    res = Nutrition()
    for s in state:
        res += s.scaled_nutrition()
    return res


DEFAULT_COEFFICIENTS = [
    100000, #1,  # Calories
    8,  # Carbohydrate
    20,  # Protein
    50,  # Total fat
    1.5 * 50,  # Saturated fat
    50,  # Trans fat

    0,  # Sugar
    0,  # Cholesterol
    0,  # Fiber
    0,  # Sodium
    0,  # Potassium
    0,  # Calcium
    0,  # Iron

    0,  # Vitamin C
    0,  # Vitamin D
    0,  # Vitamin A
]


# Source: https://en.wikipedia.org/wiki/Simulated_annealing#Overview
# https://codeforces.com/blog/entry/94437
class SimulatedAnnealing:
    def __init__(self, profile: StudentProfileSpec, state: list[PlateSectionState],
                 coefficients: tuple[float], alpha: float, smallest_temp: float, seed: int):
        """
        Creates a SimulatedAnnealing object which can run the portion-selecting algorithm
        @param
        @param state: Initial algorithm state, as a list of PlateSectionState.  For the purposes of data analysis of
        algorithm performance, each element can be constructed using the first four parameters with the rest being in
        their default state.
        @param coefficients: List of weights denoting how much each nutrient is weighted.  The cost of a state is
        determined by the distance of its nutrition facts to the 'allowed' range.  Euclidian distance**2 is the metric
        used to measure how far each nutrient is from its goal.  These are then scaled by the individual coefficients.
        See self.cost_of for more details on which coefficient affects what.
        @param alpha: Amount temperature is multiplied by after each iteration
        @param smallest_temp: Minimal temperature before algorithm termination.
        @param seed: Seed value of RNG to make run deterministic.  -1 means no set seed
        """
        # Info properties
        self.lo_req, self.hi_req = nutritional_info_for(profile)

        # Parameter properties
        self.seed = seed
        self.alpha = alpha
        self.smallest_temp = smallest_temp
        self.coefficients = coefficients

        # State properties
        self.t = 1
        self.last_nudge: tuple[int, float] = (0, 0)
        self.state: list[PlateSectionState] = state

        # Result properties
        self.done = False
        self.final_cost = -1
        self.runtime = -1

    def mid_state(self):
        """
        @return: Copies the current state except state[i].volume is at the middle value
        """
        return [state.with_mid_volume() for state in self.state]

    def lo_state(self):
        """
        @return: Copies the current state except state[i].volume is at the min value
        """
        return [state.with_min_volume() for state in self.state]

    def hi_state(self):
        """
        @return: Copies the current state except state[i].volume is at the max value
        """
        return [state.with_max_volume() for state in self.state]

    def nudge(self, t):
        """
        Nudges self.state to a random neighbour based on a given temperature
        @return: None
        """
        idx = random.randint(0, len(self.state) - 1)
        self.last_nudge = idx, self.state[idx].nudge(t * random_sign())

    def un_nudge(self):
        """
        Un-nudges self.state based on the self.last_nudge property (which is set by self.nudge(...))
        @return: None
        """
        idx, old_volume = self.last_nudge
        self.state[idx].volume = old_volume

    def cost_of(self, state):
        """
        Given a state, returns its cost, which is based on the current nutritional limits (upper and lower).
        @param state: Self-explanatory
        @return: Self-explanatory
        """
        cur_info = nutrition_of(state)
        return self.coefficients[0] * dist_sq(cur_info.calories, self.lo_req.calories, self.hi_req.calories) + \
               self.coefficients[1] * dist_sq(cur_info.carbohydrate, self.lo_req.carbohydrate, self.hi_req.carbohydrate) + \
               self.coefficients[2] * dist_sq(cur_info.protein, self.lo_req.protein, self.hi_req.protein) + \
               self.coefficients[3] * dist_sq(cur_info.total_fat, self.lo_req.total_fat, self.hi_req.total_fat) + \
               self.coefficients[4] * dist_sq(cur_info.saturated_fat, self.lo_req.saturated_fat, self.hi_req.saturated_fat) + \
               self.coefficients[5] * dist_sq(cur_info.trans_fat, self.lo_req.trans_fat, self.hi_req.trans_fat) + \
               self.coefficients[5] * dist_sq(cur_info.sugar, self.lo_req.sugar, self.hi_req.sugar) + \
               self.coefficients[6] * dist_sq(cur_info.cholesterol, self.lo_req.cholesterol, self.hi_req.cholesterol) + \
               self.coefficients[7] * dist_sq(cur_info.fiber, self.lo_req.fiber, self.hi_req.fiber) + \
               self.coefficients[8] * dist_sq(cur_info.sodium, self.lo_req.sodium, self.hi_req.sodium) + \
               self.coefficients[9] * dist_sq(cur_info.potassium, self.lo_req.potassium, self.hi_req.potassium) + \
               self.coefficients[10] * dist_sq(cur_info.calcium, self.lo_req.calcium, self.hi_req.calcium) + \
               self.coefficients[11] * dist_sq(cur_info.iron, self.lo_req.iron, self.hi_req.iron) + \
               self.coefficients[12] * dist_sq(cur_info.vitamin_c, self.lo_req.vitamin_c, self.hi_req.vitamin_c) + \
               self.coefficients[13] * dist_sq(cur_info.vitamin_d, self.lo_req.vitamin_d, self.hi_req.vitamin_d) + \
               self.coefficients[14] * dist_sq(cur_info.vitamin_a, self.lo_req.vitamin_a, self.hi_req.vitamin_a)

    def accept_probability_of(self, c_new: float, c_old: float, scale_coeff: float):
        """
        Computes the acceptance probability of a new state given the costs of the old and new state.  See
        https://en.wikipedia.org/wiki/Simulated_annealing
        @param c_new: Cost of the new state
        @param c_old: Cost of the old state
        @param scale_coeff: Coefficient to scale the cost difference by when computing acceptance probability.
        @return: Self-explanatory
        """
        return 1 if c_new <= c_old else exp(-(c_new - c_old) * scale_coeff / self.t)

    def run_algorithm(self):
        """
        Runs the algorithm
        @return: None, the result of the algorithm will be stored in the final state (self.state).  You can use
        backend.algorithm.integration to retrieve the result in a way that will be returned to the frontend.
        """
        if self.seed != -1:
            random.seed(self.seed)

        # Initialization
        cost_bound = max(self.cost_of(self.lo_state()), self.cost_of(self.hi_state()))
        scale_cost_by = 60 / (cost_bound + 0.0001)  # special case when cost_bound == 0
        self.state = self.mid_state()

        # Run algorithm
        start_time = time.perf_counter()
        t = 0.5  # Initial Temp, we only take half to full filled anyway
        while t >= self.smallest_temp:
            c_old = self.cost_of(self.state)
            self.nudge(t)
            c_new = self.cost_of(self.state)
            if self.accept_probability_of(c_new, c_old, scale_cost_by) < random.random():
                self.un_nudge()  # undo the nudge if it failed

            # update tmp
            t *= self.alpha

        # Set result vars
        self.runtime = time.perf_counter() - start_time
        self.final_cost = self.cost_of(self.state)
        self.done = True
