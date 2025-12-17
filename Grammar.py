import re as _re
import copy as _copy
import random as _random
import lark as _lark
from graphviz import Digraph

class Symbol:
    __slots__ = ("text",)
    def __init__(self, text): self.text = text
    def __repr__(self): return self.text
    def __eq__(self, other): return type(self) == type(other) and self.text == other.text
    def __hash__(self): return hash((type(self), self.text))

class NonterminalSymbol(Symbol): pass
class TerminalSymbol(Symbol): pass

class Node:
    __slots__ = ("symbol", "children")
    def __init__(self, symbol):
        self.symbol = symbol
        self.children = []

class DerivationTree:
    __slots__ = ("grammar", "root_node")
    def __init__(self, grammar, root_symbol=None):
        self.grammar = grammar
        self.root_node = Node(root_symbol or grammar.start_symbol)

    def _expand(self, node, rhs_symbols):
        new_nodes = [Node(sym) for sym in rhs_symbols]
        node.children = new_nodes
        return new_nodes

    def string(self):
        """Uses Stack-based DFS to collect leaves from Left to Right."""
        nodes = []
        stack = [self.root_node]
        while stack:
            node = stack.pop()
            if node.children:
                # Reverse children so the 'Left Child' is processed first
                stack.extend(reversed(node.children))
            else:
                nodes.append(node)
        return "".join(nd.symbol.text for nd in nodes)

class Grammar:
    __slots__ = ("nonterminal_symbols", "terminal_symbols", "production_rules", "start_symbol", "_cache")

    def __init__(self, bnf_text=None):
        self.terminal_symbols = set()
        self.nonterminal_symbols = set()
        self.production_rules = {}
        self.start_symbol = None
        self._cache = {}
        if bnf_text: self.from_bnf_text(bnf_text)

    def from_bnf_text(self, bnf_text):
        lines = [l.strip() for l in bnf_text.strip().split('\n') if l.strip()]
        for line in lines:
            if "::=" not in line: continue
            lhs_raw, rhs_raw = line.split("::=")
            lhs = NonterminalSymbol(lhs_raw.strip().strip('<>'))
            if self.start_symbol is None: self.start_symbol = lhs
            self.nonterminal_symbols.add(lhs)
            
            if lhs not in self.production_rules: self.production_rules[lhs] = []
            for alt in rhs_raw.split('|'):
                symbols = []
                tokens = _re.findall(r'<[^>]+>|"[^"]+"|\'[^\']+\'|[^\s]', alt)
                for t in tokens:
                    t = t.strip()
                    if not t: continue
                    if t.startswith('<') and t.endswith('>'):
                        sym = NonterminalSymbol(t.strip('<>'))
                        self.nonterminal_symbols.add(sym)
                    else:
                        sym = TerminalSymbol(t.strip('"').strip("'"))
                        self.terminal_symbols.add(sym)
                    symbols.append(sym) # Fix: Correct indentation to capture all symbols
                self.production_rules[lhs].append(symbols)

    def generate_derivation_tree(self, max_expansions=50, root_symbol=None):
        dt = DerivationTree(self, root_symbol)
        stack = [dt.root_node]
        expansions = 0
        while stack and expansions < max_expansions:
            curr = stack.pop(0)
            if not isinstance(curr.symbol, NonterminalSymbol): continue
            rules = self.production_rules.get(curr.symbol, [])
            if not rules: continue
            chosen_rule = _random.choice(rules)
            new_nodes = dt._expand(curr, chosen_rule)
            stack = [n for n in new_nodes if isinstance(n.symbol, NonterminalSymbol)] + stack
            expansions += 1
        return dt

    def parse_string(self, string):
        # Simplified internal call to the Lark-based DFS parser
        return parse_string_internal(self, string)

def _lark_tree_to_dt(grammar, lark_tree, nt_map_rev):
    """Recursive DFS to convert Lark tree to custom DerivationTree."""
    dt = DerivationTree(grammar)
    def build(lark_node, dt_node):
        if isinstance(lark_node, _lark.Tree):
            child_symbols = []
            for child in lark_node.children:
                if isinstance(child, _lark.Tree):
                    child_symbols.append(nt_map_rev[child.data])
                else:
                    child_symbols.append(TerminalSymbol(str(child)))
            dt_children = dt._expand(dt_node, child_symbols)
            for l_child, dt_child in zip(lark_node.children, dt_children):
                if isinstance(l_child, _lark.Tree): build(l_child, dt_child)
    build(lark_tree, dt.root_node)
    return dt

def parse_string_internal(grammar, string):
    nt_map_fwd = {nt: f"nt{i}" for i, nt in enumerate(grammar.nonterminal_symbols)}
    nt_map_rev = {f"nt{i}": nt for i, nt in enumerate(grammar.nonterminal_symbols)}
    lark_rules = []
    for lhs, rhs_list in grammar.production_rules.items():
        alts = []
        for rhs in rhs_list:
            parts = [nt_map_fwd[s] if isinstance(s, NonterminalSymbol) else f'"{s.text}"' for s in rhs]
            alts.append(" ".join(parts))
        lark_rules.append(f"{nt_map_fwd[lhs]}: " + " | ".join(alts))
    
    parser = _lark.Lark("\n".join(lark_rules), start=nt_map_fwd[grammar.start_symbol])
    return _lark_tree_to_dt(grammar, parser.parse(string), nt_map_rev)