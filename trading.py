import re as _re
import copy as _copy
import random as _random
import lark as _lark
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA, GOOG
# Risk-Adjusted Returns
# Importing your custom logic from your files
from Grammar import Grammar
from EvolutionaryAlgorithm import EvolutionaryAlgorithm, Individual

# --- 1. THE TRADING BNF ---
trading_bnf = r"""
<PROGRAM> ::= <L00> "\n" <L01> "\n" <L02> "\n" <L03> "\n" <L04> "\n" <L05> "\n" <L06> "\n" <L07> "\n" <L08> "\n" <L09> "\n" <L10> "\n" <L11> "\n" <L12> "\n" <L13>
<L00> ::= "class EvoStrat(Strategy):"
<L01> ::= "    n1 = " <NUMBER>
<L02> ::= "    n2 = " <NUMBER>
<L03> ::= "    n3 = " <NUMBER>
<L04> ::= "    n4 = " <NUMBER>
<L05> ::= "    def init(self):"
<L06> ::= "        close = self.data.Close"
<L07> ::= "        self.sma1 = self.I(SMA, close, self.n1)"
<L08> ::= "        self.sma2 = self.I(SMA, close, self.n2)"
<L09> ::= "        self.sma3 = self.I(SMA, close, self.n3)"
<L10> ::= "        self.sma4 = self.I(SMA, close, self.n4)"
<L11> ::= "    def next(self):"
<L12> ::= "        if crossover(" <VAR> ", " <VAR> "):"
<L13> ::= "            self.buy()"
<VAR> ::= "self.sma1" | "self.sma2" | "self.sma3" | "self.sma4"
<NUMBER> ::= "10" | "20" | "30" | "40" | "50" | "60" | "70" | "80" | "90"
"""

# --- 2. OBJECTIVE FUNCTION ---
def trading_objective(phenotype_string):
    namespace = {
        'Strategy': Strategy, 
        'SMA': SMA, 
        'crossover': crossover,
        'np': np
    }
    
    code = phenotype_string.replace('\\n', '\n')
    
    try:
        exec(code, namespace)
        strat = namespace['EvoStrat']
        bt = Backtest(GOOG, strat, cash=10000, commission=.002, exclusive_orders=True)
        stats = bt.run()
        
        val = stats['Sortino Ratio']
        if np.isnan(val) or val <= 0:
            return 1000.0 
        
        return -1.0 * val
    
    except Exception:
        return 2000.0

# --- 3. EXECUTION BLOCK ---
if __name__ == "__main__":
    gram = Grammar(trading_bnf)
    
    ea = EvolutionaryAlgorithm(
        grammar=gram, 
        objective_function=trading_objective, 
        population_size=15, 
        complexity_coefficient=0.01
    )
    
    print("--- STARTING TRADING STRATEGY EVOLUTION ---")
    best_ind = ea.run(gens=10)
    
    # 1. Display Best Strategy Code
    print("\n" + "="*30)
    print("BEST STRATEGY FOUND:")
    print("="*30)
    final_code = best_ind.phenotype.replace('\\n', '\n')
    print(final_code)
    
    # 2. Visualizing the Strategy Tree (Plotting)
    print("\nGenerating strategy visualization...")
    try:
        # Using the plot function from the tree
        fig = best_ind.genotype.plot() 
        fig.render("best_trading_strategy", format="png", cleanup=True)
        print("Successfully saved 'best_trading_strategy.png'")
    except Exception as e:
        print(f"Could not generate plot: {e}")

    # 3. Final Validation Performance
    print("\nRunning Final Backtest...")
    final_namespace = {'Strategy': Strategy, 'SMA': SMA, 'crossover': crossover}
    
    try:
        exec(final_code, final_namespace)
        FinalStrategyClass = final_namespace['EvoStrat']
        bt = Backtest(GOOG, FinalStrategyClass, cash=10000)
        stats = bt.run()
        
        print("\nFinal Performance Stats:")
        print("-" * 25)
        print(stats[['Return [%]', 'Sortino Ratio', 'Buy & Hold Return [%]']])
        print("-" * 25)
        
    except Exception as e:
        print(f"Final Validation failed: {e}")