from evaluations.verification import VerifyOutput, normalize_text
from verification import VerificationResult
from verification.stats import ActorsStats


class VerifyActors(VerifyOutput):
    """Verifier for actors comparing against an expected output"""

    def verify(self) -> VerificationResult[ActorsStats]:
        # Map normalized expected names to their full objects for instant lookup
        expected_names_map = {normalize_text(obj["name"]): obj for obj in self.expected_output}

        correct_fields = 0
        extra_fields = 0

        for output_obj in self.actual_output:
            obj_name = normalize_text(output_obj.get("name", ""))
            obj_type = output_obj.get("type")

            # Check if the generated work object exists in our expected map
            if obj_name in expected_names_map:
                # 1. The name matched correctly
                correct_fields += 1

                # Fetch the actual expected object using the name as the key
                expected_object = expected_names_map[obj_name]

                # 2. Go further to check if the type matches
                if obj_type == expected_object.get("type"):
                    correct_fields += 1
                else:
                    # Name matched, but type was incorrect (1 extra incorrect field)
                    extra_fields += 1
            else:
                # The entire output work object wasn't in the expected list (2 extra incorrect fields)
                extra_fields += 2
        # TODO: implement
        return VerificationResult(correct_fields, extra_fields, ActorsStats(), ActorsStats())
