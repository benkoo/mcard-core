from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class SuccessCriteria:
    verification: str
    validation: str
    performance: str

    @classmethod
    def create(cls):
        return cls(
            verification="Verification criteria for the todo.",
            validation="Validation criteria for the todo.",
            performance="Performance metrics for the todo."
        )

@dataclass
class AbstractSpecification:
    context: str
    goals: List[str]
    success_criteria: SuccessCriteria

    @classmethod
    def create(cls, context: str = "", goals: List[str] = None, success_criteria: Optional[SuccessCriteria] = None):
        return cls(
            context=context or "The spatial-temporal context of the todo.",
            goals=goals or ["A list of goal statements for the todo."],
            success_criteria=success_criteria or SuccessCriteria.create()
        )

@dataclass
class ConcreteImplementation:
    inputs: Dict[str, Any]
    activities: Dict[str, Any]
    outputs: Dict[str, Any]

    @classmethod
    def create(cls):
        return cls(
            inputs={},
            activities={},
            outputs={}
        )

@dataclass
class RealisticExpectations:
    practical_boundaries: Dict[str, Any]
    traces: List[str]
    external_feedback: Dict[str, Any]

    @classmethod
    def create(cls):
        return cls(
            practical_boundaries={},
            traces=["A list of execution traces for the todo."],
            external_feedback={}
        )

@dataclass
class CubicalLogicModel:
    abstract_spec: AbstractSpecification
    concrete_impl: ConcreteImplementation
    realistic_expectations: RealisticExpectations

    @classmethod
    def create(cls, context: str = "", goals: List[str] = None) -> 'CubicalLogicModel':
        return cls(
            abstract_spec=AbstractSpecification.create(context, goals),
            concrete_impl=ConcreteImplementation.create(),
            realistic_expectations=RealisticExpectations.create()
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "abstract_spec": {
                "context": self.abstract_spec.context,
                "goals": self.abstract_spec.goals,
                "success_criteria": {
                    "verification": self.abstract_spec.success_criteria.verification,
                    "validation": self.abstract_spec.success_criteria.validation,
                    "performance": self.abstract_spec.success_criteria.performance
                }
            },
            "concrete_impl": {
                "inputs": self.concrete_impl.inputs,
                "activities": self.concrete_impl.activities,
                "outputs": self.concrete_impl.outputs
            },
            "realistic_expectations": {
                "practical_boundaries": self.realistic_expectations.practical_boundaries,
                "traces": self.realistic_expectations.traces,
                "external_feedback": self.realistic_expectations.external_feedback
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CubicalLogicModel':
        abstract_spec = AbstractSpecification(
            context=data["abstract_spec"]["context"],
            goals=data["abstract_spec"]["goals"],
            success_criteria=SuccessCriteria(
                verification=data["abstract_spec"]["success_criteria"]["verification"],
                validation=data["abstract_spec"]["success_criteria"]["validation"],
                performance=data["abstract_spec"]["success_criteria"]["performance"]
            )
        )
        concrete_impl = ConcreteImplementation(
            inputs=data["concrete_impl"]["inputs"],
            activities=data["concrete_impl"]["activities"],
            outputs=data["concrete_impl"]["outputs"]
        )
        realistic_expectations = RealisticExpectations(
            practical_boundaries=data["realistic_expectations"]["practical_boundaries"],
            traces=data["realistic_expectations"]["traces"],
            external_feedback=data["realistic_expectations"]["external_feedback"]
        )
        return cls(abstract_spec, concrete_impl, realistic_expectations)
