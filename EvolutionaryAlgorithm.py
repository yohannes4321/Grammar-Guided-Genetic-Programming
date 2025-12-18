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

    def crossover(self, parent1, parent2):
        """Swaps compatible subtrees between two individuals."""
        # Clone to avoid modifying original parents
        tree1 = copy.deepcopy(parent1.genotype)
        tree2 = copy.deepcopy(parent2.genotype)

        # Get all non-terminal nodes (points where we can swap)
        nodes1 = [n for n in self._get_all_nodes(tree1.root_node) if n.children]
        nodes2 = [n for n in self._get_all_nodes(tree2.root_node) if n.children]

        random.shuffle(nodes1)
        for n1 in nodes1:
            # Find a node in parent 2 that has the EXACT same grammar symbol
            compatible_targets = [n2 for n2 in nodes2 if n2.symbol == n1.symbol]
            if compatible_targets:
                n2 = random.choice(compatible_targets)
                
                
                n1.children, n2.children = n2.children, n1.children
                return Individual(tree1)

    
        return self.mutate(parent1)

    def mutate(self, individual):
        """Re-generates a random branch of the derivation tree."""
        mutated_tree = copy.deepcopy(individual.genotype)
        nodes = [n for n in self._get_all_nodes(mutated_tree.root_node) if n.children]
        if nodes:
            target = random.choice(nodes)
            # Generate a new subtree starting from the same symbol
            new_subtree = self.grammar.generate_derivation_tree(root_symbol=target.symbol).root_node
            target.children = new_subtree.children
        return Individual(mutated_tree)

    def run(self, gens=10):
        """Main Evolutionary Loop."""
        # Initial Population
        self.population = [Individual(self.grammar.generate_derivation_tree()) for _ in range(self.pop_size)]
        
        for g in range(gens):
            # 1. Evaluate
            for ind in self.population: 
                if ind.fitness is None: # Only evaluate if new
                    self._evaluate(ind)
            
            # 2. Sort by fitness (lower is better)
            self.population.sort(key=lambda x: x.fitness)
            print(f"Gen {g} | Best Score: {self.population[0].fitness:.2f} | Phenotype: {self.population[0].phenotype[:50]}...")

            # 3. Create Next Generation
            next_gen = [copy.deepcopy(self.population[0])] # Elitism (keep the champion)
            
            while len(next_gen) < self.pop_size:
                # 70% chance of crossover, 30% mutation
                if random.random() < 0.7:
                    # Pick 2 parents from the top 10 individuals
                    p1, p2 = random.sample(self.population[:10], 2)
                    offspring = self.crossover(p1, p2)
                else:
                    # Pick 1 parent from the top 10 individuals
                    p = random.choice(self.population[:10])
                    offspring = self.mutate(p)
                
                next_gen.append(offspring)
            
            self.population = next_gen

        return self.population[0]