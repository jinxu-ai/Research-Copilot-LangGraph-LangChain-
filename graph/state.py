from typing import TypedDict, List

class ResearchState(TypedDict):
    """
    Typed dictionary representing the state of a research process.

    Keys:
        input (str): The initial user input or research question.
        plan (str): The research plan or strategy to follow.
        evidence (List[str]): A list of evidence or supporting information gathered.
        output (str): The final synthesized result or conclusion.
    """
    
    input: str
    plan: str
    evidence: List[str]
    output: str
