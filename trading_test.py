import unittest
import numpy as np
from Grammar import Grammar
from EvolutionaryAlgorithm import EvolutionaryAlgorithm, Individual
from trading import trading_objective 

class TestTradingEvolution(unittest.TestCase):

    def setUp(self):
        """SET UP: Preparing the Lab"""
        # A valid Trading BNF that follows Backtesting.py structure
        self.bnf = r"""
        <PROGRAM> ::= <L00> "\n" <L01> "\n" <L02> "\n" <L03>
        <L00> ::= "class EvoStrat(Strategy):"
        <L01> ::= "    n1 = 10"
        <L02> ::= "    def init(self): self.sma = self.I(SMA, self.data.Close, self.n1)"
        <L03> ::= "    def next(self): \n        if self.data.Close > self.sma: self.buy()"
        """
        self.gram = Grammar(self.bnf)
        
        # We use the REAL trading_objective (GOOG data)
        self.ea = EvolutionaryAlgorithm(
            self.gram, 
            trading_objective, 
            complexity_coefficient=0.01
        )

    def test_initialization_and_grammar(self):
      
        tree = self.gram.generate_derivation_tree()
        ind = Individual(tree)
        
        # Check if the text matches our BNF rules
        self.assertTrue(ind.phenotype.startswith("class EvoStrat"))
        self.assertIn("self.buy()", ind.phenotype)
        # Complexity should be an integer (count of characters/nodes)
        self.assertIsInstance(ind.complexity, int)

    def test_genetic_operators(self):
        """CROSSOVER & MUTATION: Testing the 'Evolutionary Machinery'"""
        p1 = Individual(self.gram.generate_derivation_tree())
        p2 = Individual(self.gram.generate_derivation_tree())
        
        # 1. Test Crossover
        child = self.ea.crossover(p1, p2)
        self.assertIsNotNone(child)
        self.assertNotEqual(child.genotype, p1.genotype)
        
        # 2. Test Mutation
        mutated = self.ea.mutate(p1)
        self.assertNotEqual(mutated.genotype, p1.genotype)

    def test_fitness_and_penalty_check(self):
        """PENALTY CHECK: Verifying the 'Filter' against Real GOOG Data"""
        # Create a "bad" individual manually to force a failure if needed
        # Or evaluate a random one to see real-world performance
        tree = self.gram.generate_derivation_tree()
        ind = Individual(tree)
        
        self.ea._evaluate(ind)
        
        # LOGIC:
        # If it's a good strategy, it should be a negative number (e.g., -1.4)
        # If it failed or lost money, it should be 1000.0 or 2000.0
        is_valid_score = ind.fitness < 0 or ind.fitness >= 1000
        self.assertTrue(is_valid_score, f"Unexpected fitness value: {ind.fitness}")

    def test_selection_logic(self):
        """SURVIVAL OF THE FITTEST: Testing the 'Ranking'"""
        pop = [Individual(self.gram.generate_derivation_tree()) for _ in range(3)]
        for ind in pop:
            self.ea._evaluate(ind)
            
        # Sort by fitness (lowest is best)
        pop.sort(key=lambda x: x.fitness)
        
        # Ensure the champion is at the front
        self.assertTrue(pop[0].fitness <= pop[1].fitness <= pop[2].fitness)

if __name__ == '__main__':
    unittest.main()