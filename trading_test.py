import unittest
import numpy as np
from trading import Grammar, EvolutionaryAlgorithm, Individual, trading_objective

class TestGGGP(unittest.TestCase):

    def setUp(self):
        self.test_bnf = """
        <START> ::= "print(" <VAL> ")"
        <VAL> ::= "1" | "2"
        """
        self.gram = Grammar(self.test_bnf)

    ## 1. Test Grammar Integrity
    def test_grammar_generation(self):
        """Check if grammar produces valid strings based on BNF."""
        tree = self.gram.generate_derivation_tree()
        phenotype = tree.string()
        self.assertIn(phenotype, ["print(1)", "print(2)"])

    ## 2. Test Complexity Penalty
    def test_complexity_penalty(self):
        """Verify that longer strings receive a worse (higher) fitness score."""
        ea = EvolutionaryAlgorithm(self.gram, lambda x: 0.0, complexity_coefficient=1.0)
        
        # Create two individuals: one short, one long
        short_ind = Individual(self.gram.generate_derivation_tree())
        short_ind.phenotype = "short" 
        short_ind.complexity = 5
        
        long_ind = Individual(self.gram.generate_derivation_tree())
        long_ind.phenotype = "very_long_string"
        long_ind.complexity = 16
        
        ea._evaluate(short_ind)
        ea._evaluate(long_ind)
        
        self.assertLess(short_ind.fitness, long_ind.fitness, "Shorter string should have better fitness")

    ## 3. Test Mutation Validity
    def test_mutation_logic(self):
        """Ensure mutation returns a new Individual object with a tree."""
        ea = EvolutionaryAlgorithm(self.gram, lambda x: 0.0)
        ind = Individual(self.gram.generate_derivation_tree())
        mutated = ea.mutate(ind)
        self.assertIsInstance(mutated, Individual)
        self.assertIsNot(ind, mutated)

    ## 4. Test Trading Objective (The 'Exec' sandbox)
    def test_trading_objective_error_handling(self):
        """Ensure the objective function catches crashing code and returns a penalty."""
        bad_code = "this is not python code"
        score = trading_objective(bad_code)
        self.assertEqual(score, 2000.0, "Objective should return penalty for syntax errors")

if __name__ == '__main__':
    unittest.main()