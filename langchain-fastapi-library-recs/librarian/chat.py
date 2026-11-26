"""The recommendation chain and per-session memory.

The chain takes the patron's message as a plain string and returns the reply as a
plain string. Everything else (history, catalog matches) is loaded inside the first step.
"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig, RunnableLambda, RunnableSequence
from langchain_openai import ChatOpenAI

from librarian.catalog import format_books, search_catalog

SYSTEM_PROMPT = """You are the reading assistant for the Alder Creek Branch Library.
Recommend books ONLY from the catalog matches below, naming title and author, and say in
a few words why each fits. Mention availability when it matters (a book with no copies on
the shelf can still be placed on hold at the desk). Keep replies under 90 words.
If the matches don't fit the request, say so and ask one short question instead of inventing books.

Catalog matches for this turn:
{matches}"""

# One list of messages per session id: the bot's memory between turns.
SESSIONS: dict[str, list[BaseMessage]] = {}


def retrieve_books(query: str) -> str:
    return format_books(search_catalog(query))


def load_turn_context(message: str, config: RunnableConfig) -> dict:
    session_id = config["configurable"]["session_id"]
    history = SESSIONS.setdefault(session_id, [])
    # Follow-ups like "something shorter" carry no topic, so search on recent patron turns too.
    recent = [m.content for m in history if isinstance(m, HumanMessage)][-2:]
    return {
        "history": history,
        "message": message,
        "matches": retrieve_books(" ".join([*recent, message])),
    }


prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), MessagesPlaceholder("history"), ("human", "{message}")]
)


def build_chain(llm=None) -> RunnableSequence:
    llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    return RunnableSequence(
        RunnableLambda(load_turn_context).with_config(run_name="load-turn-context"),
        prompt,
        llm,
        StrOutputParser(),
    )


def remember(session_id: str, message: str, reply: str) -> None:
    SESSIONS[session_id].extend([HumanMessage(message), AIMessage(reply)])
