from dataclasses import dataclass, fields, asdict

# Health goals
LOSE_WEIGHT = 'lose_weight'
BUILD_MUSCLE = 'build_muscle'
ATHLETIC_PERFORMANCE = 'athletic_performance'
IMPROVE_TONE = 'improve_tone'
IMPROVE_HEALTH = 'improve_health'

# Sex
MALE = 'male'
FEMALE = 'female'

# Activity levels
SEDENTARY = 'sedentary'
MILD = 'mild'
MODERATE = 'moderate'
HEAVY = 'heavy'
EXTREME = 'extreme'

# Different possible meals
BREAKFAST = 'breakfast'
MORN_SNACK = 'morning_snack'
LUNCH = 'lunch'
AFT_SNACK = 'afternoon_snack'
DINNER = 'dinner'
EVE_SNACK = 'evening_snack'

# Category (of food)
VEGETABLE = 'vegetable'
PROTEIN = 'protein'
GRAINS = 'grain'


@dataclass
class Nutrition:
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

    @classmethod
    def from_object(cls, obj):
        """
        Creates a Nutrition object from any other object that has the same attributes.  Does not do type checking
        @param obj Object to initialize from
        """
        field_dict = {}
        for prop in fields(Nutrition):
            field_dict[prop.name] = getattr(obj, prop.name)
        return cls(**field_dict)

    def as_dict(self):
        return asdict(self)

    # speed?
    # this is bad coding I know
    # http://threecop1.blogspot.com/2011/04/python-3x-does-setattr-and-getattr-slow.html
    def __iadd__(self, other):
        self.calories += other.calories
        self.carbohydrate += other.carbohydrate
        self.protein += other.protein
        self.total_fat += other.total_fat
        self.saturated_fat += other.saturated_fat
        self.trans_fat += other.trans_fat

        self.sugar += other.sugar
        self.cholesterol += other.cholesterol
        self.fiber += other.fiber
        self.sodium += other.sodium
        self.potassium += other.potassium
        self.calcium += other.calcium
        self.iron += other.iron

        self.vitamin_a += other.vitamin_a
        self.vitamin_c += other.vitamin_c
        self.vitamin_d += other.vitamin_d

        return self

    def __isub__(self, other):
        self.calories -= other.calories
        self.carbohydrate -= other.carbohydrate
        self.protein -= other.protein
        self.total_fat -= other.total_fat
        self.saturated_fat -= other.saturated_fat
        self.trans_fat -= other.trans_fat

        self.sugar -= other.sugar
        self.cholesterol -= other.cholesterol
        self.fiber -= other.fiber
        self.sodium -= other.sodium
        self.potassium -= other.potassium
        self.calcium -= other.calcium
        self.iron -= other.iron

        self.vitamin_a -= other.vitamin_a
        self.vitamin_c -= other.vitamin_c
        self.vitamin_d -= other.vitamin_d

        return self

    def __imul__(self, c):
        self.calories *= c
        self.carbohydrate *= c
        self.protein *= c
        self.total_fat *= c
        self.saturated_fat *= c
        self.trans_fat *= c

        self.sugar *= c
        self.cholesterol *= c
        self.fiber *= c
        self.sodium *= c
        self.potassium *= c
        self.calcium *= c
        self.iron *= c

        self.vitamin_a *= c
        self.vitamin_c *= c
        self.vitamin_d *= c

        return self

    def __itruediv__(self, c):
        self.calories /= c
        self.carbohydrate /= c
        self.protein /= c
        self.total_fat /= c
        self.saturated_fat /= c
        self.trans_fat /= c

        self.sugar /= c
        self.cholesterol /= c
        self.fiber /= c
        self.sodium /= c
        self.potassium /= c
        self.calcium /= c
        self.iron /= c

        self.vitamin_a /= c
        self.vitamin_c /= c
        self.vitamin_d /= c

        return self

    def copy(self):
        return Nutrition(calories=self.calories,
                         carbohydrate=self.carbohydrate,
                         protein=self.protein,
                         total_fat=self.total_fat,
                         saturated_fat=self.saturated_fat,
                         trans_fat=self.trans_fat,
                         sugar=self.sugar,
                         cholesterol=self.cholesterol,
                         fiber=self.fiber,
                         sodium=self.sodium,
                         potassium=self.potassium,
                         calcium=self.calcium,
                         iron=self.iron,
                         vitamin_a=self.vitamin_a,
                         vitamin_c=self.vitamin_c,
                         vitamin_d=self.vitamin_d)

    def __add__(self, other):
        ret = self.copy()
        ret += other
        return ret

    def __sub__(self, other):
        ret = self.copy()
        ret -= other
        return ret

    def __mul__(self, c):
        ret = self.copy()
        ret *= c
        return ret

    def __truediv__(self, c):
        ret = self.copy()
        ret /= c
        return ret
