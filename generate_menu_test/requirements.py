import datetime
from dataclasses import dataclass

from common import Nutrition, SEDENTARY, MILD, MODERATE, HEAVY, EXTREME, MALE, FEMALE, BUILD_MUSCLE, \
    ATHLETIC_PERFORMANCE, LOSE_WEIGHT, IMPROVE_TONE, IMPROVE_HEALTH

# JSON does not support infinity
INF = 10 ** 20

# https://www.notion.so/weplate/Mathematical-Calculations-f561b494f2444cfc87023ef615cf2bea#a976edca5f394d26b536704ff6f691ce
DEFAULT_LO_REQS = dict(
    # Macro
    calories=-1,
    carbohydrate=-1,
    protein=-1,
    total_fat=-1,
    saturated_fat=-1,
    trans_fat=0,

    # Micro
    sugar=-INF,
    cholesterol=-INF,
    fiber=30,
    sodium=1500,
    potassium=3000,
    calcium=1000,
    iron=8,
    vitamin_d=600,
    vitamin_c=90,
    vitamin_a=3000,
)

DEFAULT_HI_REQS = dict(
    # Macro
    calories=-1,
    carbohydrate=-1,
    protein=-1,
    total_fat=-1,
    saturated_fat=-1,
    trans_fat=0,

    # Micro
    sugar=27,
    cholesterol=300,
    fiber=INF,
    sodium=4000,
    potassium=INF,
    calcium=2500,
    iron=45,
    vitamin_d=4000,
    vitamin_c=2000,
    vitamin_a=10000,
)

# Calorie coefficients
ACTIVITY_LEVEL_COEFF = {
    SEDENTARY: 1.2,
    MILD: 1.3,
    MODERATE: 1.5,
    HEAVY: 1.7,
    EXTREME: 1.9,
}

# https://www.notion.so/weplate/Mathematical-Calculations-f561b494f2444cfc87023ef615cf2bea#a976edca5f394d26b536704ff6f691ce
# Base, Weight, Height, Age
SEX_COEFF = {
    MALE: (88.362, 13.397, 4.799, 5.677),
    FEMALE: (447.593, 9.247, 3.098, 4.330)
}

# https://www.notion.so/weplate/Mathematical-Calculations-f561b494f2444cfc87023ef615cf2bea#72d92545467d40faa8508132432618c8
# Protein, Carb, Fat, Saturated Fat - Each item is a tuple (lo, hi)
# For protein and carb, the % are based on body weight
# For fat and saturated fat, the % are based on total caloric intake (/9 as fat is 9 cal/g)
MACROS_COEFF = {
    BUILD_MUSCLE: ((1.5, 1.8), (6, 6.6), (0.3, 0.35), (0, 0.1)),
    ATHLETIC_PERFORMANCE: ((0.9, 1.05), (6, 6.6), (0.3, 0.35), (0, 0.1)),
    LOSE_WEIGHT: ((1.1, 1.3), (5, 5.5), (0.2, 0.25), (0, 0.1)),
    IMPROVE_TONE: ((0.8, 1), (6, 6.3), (0.25, 0.3), (0, 0.1)),
    IMPROVE_HEALTH: ((0.8, 1), (5, 6), (0.2, 0.25), (0, 0.1))
}

# https://www.notion.so/weplate/Mathematical-Calculations-f561b494f2444cfc87023ef615cf2bea#422b95b3b18c47dbbbee6eec642ee779
# Max portion sizes and min fill requirement, in ML
CALS_IN_FAT = 9


# ProfileSpec
@dataclass
class StudentProfileSpec:
    height: float
    weight: float
    birthdate: datetime.date
    meals: list[str]
    meal_length: float

    sex: str
    health_goal: str
    activity_level: str


def nutritional_info_for(profile: StudentProfileSpec) -> tuple[Nutrition, Nutrition]:
    for req_prop in ('activity_level', 'sex', 'weight', 'height', 'birthdate'):
        if not hasattr(profile, req_prop):
            raise ValueError(f'Student profile missing attribute {req_prop}')

    # Formulae: https://www.notion.so/weplate/Mathematical-Calculations-f561b494f2444cfc87023ef615cf2bea:w
    c_base, c_weight, c_height, c_age = SEX_COEFF[profile.sex]
    c_activity = ACTIVITY_LEVEL_COEFF[profile.activity_level]
    age = (datetime.date.today() - profile.birthdate).days // 365  # Leap years are fake news
    lo = Nutrition(**DEFAULT_LO_REQS)
    hi = Nutrition(**DEFAULT_HI_REQS)

    # Set calorie count
    calories = (c_base + c_weight * profile.weight + c_height * profile.height - c_age * age) * c_activity * 1.1
    if profile.health_goal == LOSE_WEIGHT:
        calories -= 250
    elif profile.health_goal == BUILD_MUSCLE:
        calories += 250
    lo.calories = calories * 0.85  # Have some leeway
    hi.calories = calories * 1.15

    # Set Macros count
    protein, carb, fat, sat_fat = MACROS_COEFF[profile.health_goal]
    lo.protein = protein[0] * profile.weight
    hi.protein = protein[1] * profile.weight
    lo.carbohydrate = carb[0] * profile.weight
    hi.carbohydrate = carb[1] * profile.weight
    # Use exact calorie requirements
    lo.total_fat = fat[0] * calories / CALS_IN_FAT
    hi.total_fat = fat[1] * calories / CALS_IN_FAT
    lo.saturated_fat = sat_fat[0] * calories / CALS_IN_FAT
    hi.saturated_fat = sat_fat[1] * calories / CALS_IN_FAT

    # Divide reqs by 3 since these are daily
    for prop in DEFAULT_HI_REQS.keys():  # Doesn't matter if hi or lo
        setattr(lo, prop, getattr(lo, prop) / 3)
        setattr(hi, prop, getattr(hi, prop) / 3)

    return lo, hi
