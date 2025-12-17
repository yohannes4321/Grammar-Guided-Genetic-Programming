import unittest
import numpy as np
from Grammar import Grammar
from EvolutionaryAlgorithm import EvolutionaryAlgorithm, Individual
from trading import trading_objective

class TestGGGPFullPipeline(unittest.TestCase):

    def setUp(self):
        # A simple trading-style BNF for testing
        self.bnf = r"""
        <S> ::= "if " <VAR> " > " <VAR> ": self.buy()"
        <VAR> ::= "self.sma1" | "self.sma2" | "self.close"
        """
        self.gram = Grammar(self.bnf)
        # Mock objective function (returns 0.0 fitness)
        self.ea = EvolutionaryAlgorithm(self.gram, lambda x: 0.0, complexity_coefficient=0.01)

    def test_random_initialization(self):
        """Step 1: Verify the population starts with valid random phenotypes."""
        pop = [Individual(self.gram.generate_derivation_tree()) for _ in range(5)]
        for ind in pop:
            self.assertTrue(ind.phenotype.startswith("if "))
            self.assertTrue(ind.phenotype.endswith(": self.buy()"))
            self.assertIsInstance(ind.complexity, int)

    def test_crossover_logic(self):
        """Step 2: Verify crossover produces a new valid individual from two parents."""
        p1 = Individual(self.gram.generate_derivation_tree())
        p2 = Individual(self.gram.generate_derivation_tree())
        
        offspring = self.ea.crossover(p1, p2)
        
        self.assertIsInstance(offspring, Individual)
        # Ensure offspring phenotype is still valid according to grammar
        self.assertTrue(offspring.phenotype.startswith("if "))
        # Check that offspring is a unique object
        self.assertIsNot(offspring, p1)
        self.assertIsNot(offspring, p2)

    def test_mutation_logic(self):
        """Step 3: Verify mutation modifies the individual but stays within grammar rules."""
        ind = Individual(self.gram.generate_derivation_tree())
        old_phenotype = ind.phenotype
        
        # Mutate until the string changes (to prove mutation happened)
        mutated = ind
        for _ in range(10): 
            mutated = self.ea.mutate(ind)
            if mutated.phenotype != old_phenotype:
                break
        
        self.assertIsInstance(mutated, Individual)
        self.assertTrue(mutated.phenotype.startswith("if "))
        self.assertNotEqual(mutated.genotype, ind.genotype)

    def test_full_evaluation_with_complexity(self):
        """Step 4: Verify the penalty for complexity is added to the objective score."""
        ea_penalty = EvolutionaryAlgorithm(self.gram, lambda x: -10.0, complexity_coefficient=1.0)
        ind = Individual(self.gram.generate_derivation_tree())
        
        ea_penalty._evaluate(ind)
        # Expected fitness = objective_score (-10.0) + (char_count * 1.0)
        expected = -10.0 + ind.complexity
        self.assertAlmostEqual(ind.fitness, expected)

if __name__ == '__main__':
    unittest.main()