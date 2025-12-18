import re as _re
import copy as _copy
import random as _random
import lark as _lark
from graphviz import Digraph
from itertools import product as _cartesian_product


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
        
        nodes = []
        stack = [self.root_node]
        while stack:
            node = stack.pop()
            if node.children:
                stack.extend(reversed(node.children))
            else:
                nodes.append(node)
        return "".join(nd.symbol.text for nd in nodes)

    def to_parenthesis(self):
        def _recurse(node):
            label = f"<{node.symbol.text}>" if isinstance(node.symbol, NonterminalSymbol) else node.symbol.text
            if not node.children: return label
            return f"{label}(" + "".join(_recurse(c) for c in node.children) + ")"
        return _recurse(self.root_node)

    def plot(self, **kwargs):
        return create_graphviz_tree(self, **kwargs)

# --- The Grammar Class ---

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
                    symbols.append(sym)
                self.production_rules[lhs].append(symbols)

    def generate_derivation_tree(self, max_expansions=100, reduction_factor=0.9, root_symbol=None):
        """Generates a tree using weights that reduce over time to force termination."""
        initial_weights = {lhs: [1.0 for _ in rhs_list] for lhs, rhs_list in self.production_rules.items()}
        dt = DerivationTree(self, root_symbol)
        # Stack stores (node, current_weights)
        stack = [(dt.root_node, initial_weights)]
        expansion_counter = 0
        
        while stack and expansion_counter < max_expansions:
            curr_node, weights = stack.pop(0) 
            lhs = curr_node.symbol
            if not isinstance(lhs, NonterminalSymbol): continue
            
            rules = self.production_rules.get(lhs, [])
            if not rules: continue
            
            # Weighted random choice
            rule_weights = weights[lhs]
            total_w = sum(rule_weights)
            r = _random.uniform(0, total_w)
            upto = 0
            chosen_idx = 0
            for i, w in enumerate(rule_weights):
                if upto + w >= r:
                    chosen_idx = i
                    break
                upto += w
            
            chosen_rule = rules[chosen_idx]
            # Reduce weight of the chosen rule for future recursive calls to prevent infinite loops
            new_weights = _copy.deepcopy(weights)
            new_weights[lhs][chosen_idx] *= reduction_factor
            
            new_nodes = dt._expand(curr_node, chosen_rule)
            new_items = [(n, new_weights) for n in new_nodes if isinstance(n.symbol, NonterminalSymbol)]
            stack = new_items + stack 
            expansion_counter += 1
        return dt

    def parse_string(self, string, parser="earley"):
        return parse_string_internal(self, string, parser)

    def _lookup_or_calc(self, category, key, func, *args):
        full_key = (category, key)
        if full_key not in self._cache:
            self._cache[full_key] = func(*args)
        return self._cache[full_key]

# --- Visualization Helper ---

class _AutoCounter:
    def __init__(self):
        self.map = {}
        self.cnt = 0
    def __getitem__(self, key):
        if key not in self.map:
            self.map[key] = self.cnt
            self.cnt += 1
        return self.map[key]

def create_graphviz_tree(tree, fontname="Arial", fontsize="12"):
    dot = Digraph(node_attr={'fontname': fontname, 'fontsize': fontsize})
    cnt = _AutoCounter()
    stack = [tree.root_node]
    while stack:
        curr = stack.pop(0)
        curr_id = str(cnt[curr])
        label = curr.symbol.text if curr.symbol.text else "ε"
        if isinstance(curr.symbol, NonterminalSymbol):
            dot.node(curr_id, label, shape="box", style="filled", fillcolor="#ffe3e3")
        else:
            dot.node(curr_id, label, shape="ellipse", style="filled", fillcolor="#e3ffe3")
        for child in curr.children:
            child_id = str(cnt[child])
            dot.edge(curr_id, child_id)
            stack.append(child)
    return dot

# --- Parsing Logic ---

def parse_string_internal(grammar, string, parser_type):
    # Cache the Lark parser and maps
    lark_parser, nt_map_rev = grammar._lookup_or_calc(
        "lark", parser_type, _calc_lark_components, grammar, parser_type
    )

    try:
        lark_tree = lark_parser.parse(string)
        return _lark_tree_to_dt(grammar, lark_tree, nt_map_rev)
    except Exception as e:
        raise ValueError(f"Parsing failed: {e}")

def _calc_lark_components(grammar, parser_type):
    nt_map_fwd = {nt: f"nt{i}" for i, nt in enumerate(grammar.nonterminal_symbols)}
    nt_map_rev = {f"nt{i}": nt for i, nt in enumerate(grammar.nonterminal_symbols)}
    
    lark_rules = []
    lark_rules.append("%import common.WS")
    lark_rules.append("%ignore WS")
    for lhs, rhs_list in grammar.production_rules.items():
        alts = []
        for rhs in rhs_list:
            parts = []
            for sym in rhs:
                if isinstance(sym, NonterminalSymbol):
                    parts.append(nt_map_fwd[sym])
                else:
                    escaped = sym.text.replace('"', '\\"')
                    parts.append(f'"{escaped}"')
            alts.append(" ".join(parts))
        lark_rules.append(f"{nt_map_fwd[lhs]}: " + " | ".join(alts))
    
    lark_parser = _lark.Lark(
        "\n".join(lark_rules), 
        start=nt_map_fwd[grammar.start_symbol], 
        parser=parser_type
    )
    return lark_parser, nt_map_rev

def _lark_tree_to_dt(grammar, lark_tree, nt_map_rev):
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
                build(l_child, dt_child)
    
    build(lark_tree, dt.root_node)
    return dt

# --- Testing the implementation ---

if __name__ == "__main__":
    # 1. Random Generation Example
    math_bnf = "<S> ::= <S>+<S> | <S>*<S> | x | y"
    gram = Grammar(math_bnf)
    tree = gram.generate_derivation_tree(max_expansions=10)
    
    print("--- Generated Tree ---")
    print("String:", tree.string())
    print("Parenthesis:", tree.to_parenthesis())
    
    # 2. Parsing Example
   
    num_bnf = """
    <sentence> ::= <nounphrase> <verbphrase>

    <nounphrase> ::= <det> <noun>

    <verbphrase> ::= <verb> <nounphrase>
                | <verb>

    <det> ::= "the" | "a"
    <noun> ::= "cat" | "dog"
    <verb> ::= "sees" | "likes"
    """

    num_gram = Grammar(num_bnf)
    parsed = num_gram.parse_string("thecatseesadog")
    
    print("\n--- Parsed Tree ---")
    print("String:", parsed.string())
    
    # Visualisation (uncomment if you have Graphviz installed)
    parsed.plot().render("parsed_output", format="png", cleanup=True)