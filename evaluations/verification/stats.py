from abc import ABC


class StatsItem:
    def __init__(self):
        self.total = 0
        self.details = []

    def add_detail(self, detail: str) -> None:
        self.details.append(detail)

    def extend_details(self, details: set | list) -> None:
        self.details.extend(details)

    def increase_total(self, occurrences: int = 1) -> None:
        self.total += occurrences


class Stats(ABC):
    def __init__(self):
        self.total = 0
        self.__fields: dict[str, StatsItem] = {}

    def increase_total(self, occurrences: int = 1) -> None:
        self.total += occurrences

    def _init_fields(self, *field_names: str) -> None:
        for field_name in field_names:
            self._register_field(field_name)

    def _register_field(self, field_name: str) -> None:
        """registers a field for the stats. Overwrites if it exists"""
        self.__fields[field_name] = StatsItem()

    def _get_field(self, field_name: str) -> StatsItem:
        return self.__fields[field_name]


class WorkObjectStats(Stats):
    WORK_OBJECT_FIELD = "work_object"
    WORK_OBJECT_INSTANCE_FIELD = "work_object_instances"
    NOTE_FIELD = "note"

    def __init__(self):
        super().__init__()
        self._init_fields(
            self.WORK_OBJECT_FIELD,
            self.WORK_OBJECT_INSTANCE_FIELD,
            self.NOTE_FIELD,
        )

    @property
    def work_objects(self) -> StatsItem:
        return self._get_field(self.WORK_OBJECT_FIELD)

    @property
    def work_object_instances(self) -> StatsItem:
        return self._get_field(self.WORK_OBJECT_INSTANCE_FIELD)

    @property
    def note_filed(self) -> StatsItem:
        return self._get_field(self.NOTE_FIELD)


class ActivitiesStats(Stats):
    STEP_FIELD = "step"
    MAIN_ACTIVITY_FIELD = "main_activity"
    SUB_ACTIVITIES_FIELD = "sub_activities"

    def __init__(self):
        super().__init__()
        self._init_fields(
            self.MAIN_ACTIVITY_FIELD,
            self.SUB_ACTIVITIES_FIELD,
        )

    @property
    def step(self) -> StatsItem:
        return self._get_field(self.STEP_FIELD)

    @property
    def main_activity(self) -> StatsItem:
        return self._get_field(self.MAIN_ACTIVITY_FIELD)

    @property
    def sub_activities(self) -> StatsItem:
        return self._get_field(self.SUB_ACTIVITIES_FIELD)


class ActorsStats(Stats):
    pass
