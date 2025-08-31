from graphviz import Digraph

# Create a directed graph
dot = Digraph(comment="Research Copilot Architecture")
dot.attr(rankdir="LR", size="8")

# Define nodes
dot.node("plan", "Plan\n(LLM+JSON Parser)", shape="box", style="rounded,filled", color="lightblue")
dot.node("search", "Search\n(Web Search Tool)", shape="box", style="rounded,filled", color="lightgreen")
dot.node("select", "Select\n(Source Ranking)", shape="box", style="rounded,filled", color="lightyellow")
dot.node("read", "Read\n(PDF/HTML Loader+Splitter)", shape="box", style="rounded,filled", color="lightpink")
dot.node("synthesize", "Synthesize\n(Map-Reduce + Pydantic Notes)", shape="box", style="rounded,filled", color="lightgrey")
dot.node("decide", "Decide\n(Evidence Check)", shape="diamond", style="filled", color="orange")
dot.node("write", "Write\n(Markdown Export)", shape="box", style="rounded,filled", color="lightblue")
dot.node("end", "END", shape="oval", style="filled", color="black", fontcolor="white")

# Define edges
dot.edge("plan", "search")
dot.edge("search", "select")
dot.edge("select", "read")
dot.edge("read", "synthesize")
dot.edge("synthesize", "decide")
dot.edge("decide", "write", label="enough evidence")
dot.edge("decide", "search", label="need more evidence")
dot.edge("write", "end")

# Render diagram
file_path = "/mnt/data/research_copilot_architecture"
dot.render(file_path, format="png", cleanup=True)
file_path + ".png"
