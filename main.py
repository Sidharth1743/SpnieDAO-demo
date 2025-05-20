from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.loaders import UnstructuredIO
from camel.storages import Neo4jGraph
from knowledgeGraph import KnowledgeGraphAgent
import os

# Set up Neo4j instance
n4j = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password="0123456789",
)

# Set up model
openai = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4,
    api_key=os.environ.get("OPENAI_API_KEY"),
    model_config_dict={"temperature": 0.4}
)

# Initialize agent and I/O
uio = UnstructuredIO()
kg_agent = KnowledgeGraphAgent(model=openai)

# Read content
with open('sample_input.txt', 'r', encoding="utf-8") as file:
    text_example = file.read()

# Split into manageable chunks (by paragraph or N words)
def chunk_text(text, max_words=300):
    words = text.split()
    for i in range(0, len(words), max_words):
        yield ' '.join(words[i:i + max_words])

# Collect all graph elements
all_graph_elements = []

for idx, chunk in enumerate(chunk_text(text_example)):
    print(f"Processing chunk {idx + 1}...")
    element = uio.create_element_from_text(text=chunk, element_id=str(idx))

    try:
        graph_elements = kg_agent.run(element, parse_graph_elements=True)
        all_graph_elements.append(graph_elements)
    except Exception as e:
        print(f"Error in chunk {idx + 1}: {e}")

# Merge and insert into Neo4j
for graph in all_graph_elements:
    if graph:
        n4j.add_graph_elements(graph_elements=[graph])
