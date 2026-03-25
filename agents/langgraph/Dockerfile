# The langchain/langgraph-api image IS the Agent Server runtime.
# It provides: FastAPI, task queue, A2A endpoints, postgres checkpointing.
# We add our graph code and requirements on top.
FROM langchain/langgraph-api:python3.12

# Install our graph's Python dependencies
# (langchain-openai, etc. — must be compatible with the base image's versions)
ADD requirements.txt /deps/requirements.txt
RUN pip install --no-cache-dir -r /deps/requirements.txt

# Copy graph code to the deps folder expected by the Agent Server
ADD . /deps/langgraph-rhyme

# The LANGSERVE_GRAPHS env var (or langgraph.json) tells the server which graphs to load
# This is set in docker-compose.yml via environment or the langgraph.json mount
