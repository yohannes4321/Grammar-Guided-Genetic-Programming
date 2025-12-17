import random
import copy

class Individual:
    def __init__(self, genotype):
        self.genotype = genotype
        self.phenotype = genotype.string()
        self.fitness = None
        self.complexity = len(self.phenotype)

class EvolutionaryAlgorithm:
    def __init__(self, grammar, objective_function, population_size=20, complexity_coefficient=0.1):
        self.grammar = grammar
        self.obj_func = objective_function
        self.pop_size = population_size
        self.penalty_coeff = complexity_coefficient
        self.population = []

    def _evaluate(self, individual):
        raw_score = self.obj_func(individual.phenotype)
        penalty = individual.complexity * self.penalty_coeff
        individual.fitness = raw_score + penalty

    def _get_all_nodes(self, node):
        """Recursive DFS to find all mutation/crossover points."""
        nodes = [node]
        for child in node.children:
            nodes.extend(self._get_all_nodes(child))
        return nodes

    def mutate(self, individual):
        mutated_tree = copy.deepcopy(individual.genotype)
        nodes = [n for n in self._get_all_nodes(mutated_tree.root_node) if n.children]
        if nodes:
            target = random.choice(nodes)
            new_subtree = self.grammar.generate_derivation_tree(root_symbol=target.symbol).root_node
            target.children = new_subtree.children
        return Individual(mutated_tree)

    def run(self, gens=10):
        self.population = [Individual(self.grammar.generate_derivation_tree()) for _ in range(self.pop_size)]
        for g in range(gens):
            for ind in self.population: self._evaluate(ind)
            self.population.sort(key=lambda x: x.fitness)
            print(f"Gen {g} | Best: {self.population[0].phenotype} (Fit: {self.population[0].fitness:.2f})")
            
            # Simple Selection & Mutation
            next_gen = [copy.deepcopy(self.population[0])]
            while len(next_gen) < self.pop_size:
                parent = random.choice(self.population[:5])
                next_gen.append(self.mutate(parent))
            self.population = next_gen
        return self.population[0]