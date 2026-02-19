from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

document_analyzer_prompt = ChatPromptTemplate.from_template(
    """
    You are a highly capable assistant trained to analyze and summarize documents.
    Return ONLY valid JSON matching the exact schema below.

    {format_instructions}

    Analyze the following document content:
    {document_content}
    """)


document_comparison_prompt = ChatPromptTemplate.from_template(
    """
    You will bw provided with content from two PDFs. Your Tasks are as follows:
    
    1. Comppare the content of two PDFs.
    2. Idefntify the difference in pdf and note down the page number.
    3. The output you provide must be page wise comparison content.
    4. if any page do not have any change, mention "No Change" for that page.
    
    Input documents:
    
    {combined_docs}
    
    your Response should follow this format:
    
    {format_instructions}
    """)


# Prompt for contextual question rewriting
contextualize_question_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "given a conversation history and the most recent user query, rewrite the question as a standalone question "
        "that make sense without relying on the previous context. Do not provide an answer only reformulate the question if necessary;otherwise return it unchanged."
    )),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}")
])


# Prompt for answering based on context
context_qa_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "you are an assistant designed to answer questions using the provided context. Rely only on the retrieved "
        "information to form your response. if the answer is not found in the context, respond with 'I don't know.' "
        "keep your answer concise and no longer than 5 to 8 sentences.\n\n{context}"
    )),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}")
])


# Central dictionary to register prompts
PROMPT_REGISTRY = {
    "document_analyzer_prompt": document_analyzer_prompt,
    "document_comparison_prompt": document_comparison_prompt,
    "contextualize_question": contextualize_question_prompt,
    "context_qa": context_qa_prompt

}