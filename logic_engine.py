# logic_engine.py  -  Lab 07: Logical Reasoning & Inference
"""A tiny propositional Knowledge Base with a Forward Chaining inference engine.

Facts are plain strings (e.g. "TargetVisible").
Rules are Horn clauses stored as (premises, conclusion), meaning:
    premise_1 AND premise_2 AND ... => conclusion
"""


class KnowledgeBase:
    def __init__(self):
        self.facts = set()   # unique facts currently known to be true
        self.rules = []      # list of (list_of_premises, conclusion) tuples

    # ---------------- TELL ----------------
    def tell_fact(self, fact_string):
        """Add a fact (a percept or a deduced truth) to the KB."""
        self.facts.add(fact_string)

    def tell_rule(self, premise_list, conclusion_string):
        """Add a Horn clause:  premises (ANDed together)  =>  conclusion."""
        self.rules.append((list(premise_list), conclusion_string))

    def clear_facts(self):
        """Forget all facts but keep the rules (used before checking each tile)."""
        self.facts.clear()

    # ---------------- INFERENCE ----------------
    def forward_chain(self):
        """Data-driven forward chaining.

        Keep sweeping over the rules. Whenever every premise of a rule is already a
        known fact, add its conclusion (Modus Ponens). Stop when a full pass over
        all rules adds nothing new (a fixed point has been reached).
        """
        new_facts_added = True

        while new_facts_added:
            new_facts_added = False

            for premises, conclusion in self.rules:
                if conclusion not in self.facts:
                    # Modus Ponens check: are ALL premises true?
                    if all(p in self.facts for p in premises):
                        self.facts.add(conclusion)
                        new_facts_added = True
